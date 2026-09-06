from __future__ import annotations

import json
import os
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from book_builder import (
    AppConfig,
    build_graph_from_book_json,
    build_markdown_document,
    build_latex_document,
    compile_pdf,
    export_markdown,
    generate_book_json_from_txt,
    generate_contents,
    load_graph_json,
    save_graph_json,
    subdivide_graph,
)
from openrouter_llm import LLMConfig, OpenRouterLLM
from autogenbook.audit.latex_auditor import AuditorConfig, audit_latex
from autogenbook.audit.types import AuditSeverity
from autogenbook.llm_usage import log_usage, write_run_meta
from autogenbook.prompts.agent_prompts import render
from autogenbook.prompts.book_loader import load_book_prompts
from autogenbook.prompts.registry import get_prompt, set_prompt_registry
from rag_kb import KnowledgeBase
from autogenbook.retrieval.kb_citations import build_kb_index, kb_cite_key
from autogenbook.retrieval.manager import RetrievalManager

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_json_env(name: str) -> Any:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _apply_prompt_overrides(prompts: Dict[str, str]) -> Dict[str, str]:
    """Překryje výchozí prompty globálními (soubor global_prompts.json) a projektovými (env)."""
    merged = dict(prompts)
    global_file = REPO_ROOT / "global_prompts.json"
    if global_file.exists():
        try:
            g = json.loads(global_file.read_text(encoding="utf-8"))
            if isinstance(g, dict):
                for k, v in g.items():
                    if isinstance(v, str) and v.strip():
                        merged[k] = v
        except Exception:
            pass
    env_ovr = _load_json_env("AUTOGENBOOK_PROMPT_OVERRIDES")
    if isinstance(env_ovr, dict):
        for k, v in env_ovr.items():
            if isinstance(v, str) and v.strip():
                merged[k] = v
    return merged
from autogenbook.retrieval.mcp_papers import MCPPaperRetriever
from autogenbook.retrieval.tavily import TavilyRetriever
from utils import extract_first_json_object

from ..state import RunContext


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_input_path(value: Any) -> Optional[Path]:
    if value is None:
        return None
    try:
        return Path(str(value)).expanduser().resolve()
    except Exception:
        return None


def _ask_choice(prompt: str, choices: Dict[str, str], default: str) -> str:
    keys = "/".join([k.upper() for k in choices.keys()])
    if os.environ.get("AUTOGENBOOK_NONINTERACTIVE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return default.lower()
    while True:
        ans = input(f"{prompt} [{keys}] (default {default.upper()}): ").strip().lower()
        if not ans:
            ans = default.lower()
        if ans in choices:
            return ans


def _ask_yes_no(prompt: str, default: str = "y") -> bool:
    default = default.lower()
    if os.environ.get("AUTOGENBOOK_ASSUME_YES", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    if os.environ.get("AUTOGENBOOK_NONINTERACTIVE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return default in {"y", "yes"}
    while True:
        ans = input(f"{prompt} [Y/N] (default {default.upper()}): ").strip().lower()
        if not ans:
            ans = default
        if ans in {"y", "yes"}:
            return True
        if ans in {"n", "no"}:
            return False


def _ask_text(prompt: str, default: Optional[str] = None, required: bool = False) -> str:
    suffix = f" (default {default})" if default else ""
    if os.environ.get("AUTOGENBOOK_NONINTERACTIVE", "").strip().lower() in {"1", "true", "yes", "on"}:
        return default or ""
    while True:
        ans = input(f"{prompt}{suffix}: ").strip()
        if ans:
            return ans
        if default:
            return default
        if not required:
            return ""
        print("Zadejte prosim hodnotu.")


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs:
        return f"{hrs}h {mins}m {sec}s"
    if mins:
        return f"{mins}m {sec}s"
    return f"{sec}s"


def _revise_book_json_for_redundancy(
    book_json: dict,
    out_dir: Path,
) -> Tuple[Optional[dict], int, Optional[float]]:
    prompt_template = get_prompt("book_redundancy_user")
    prompt = render(
        prompt_template,
        book_json=json.dumps(book_json, ensure_ascii=False, indent=2),
    )

    llm = OpenRouterLLM(
        LLMConfig(
            model="openai/gpt-5-pro",
            temperature=0.2,
        )
    )
    content = llm.chat(
        [
            {"role": "system", "content": get_prompt("book_redundancy_system")},
            {"role": "user", "content": prompt},
        ],
        allow_tools=False,
    )
    usage = llm.get_last_usage()
    if usage:
        print(llm.format_usage_line(usage, label="redundancy"))
        log_usage(out_dir, "redundancy", llm, usage, {"stage": "book_json"})
    try:
        revised = extract_first_json_object(content)
        return revised, llm.get_total_tokens(), llm.get_total_cost_usd()
    except Exception:
        return None, llm.get_total_tokens(), llm.get_total_cost_usd()


def _serialize_args(args: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in vars(args).items():
        if key == "run_ctx":
            continue
        if isinstance(value, Path):
            out[key] = str(value)
        else:
            try:
                json.dumps(value)
                out[key] = value
            except TypeError:
                out[key] = str(value)
    return out


def _write_run_meta(
    run_ctx: RunContext,
    args: Any,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    error: Optional[str],
    llm: Optional[OpenRouterLLM],
    redundancy_tokens: int,
    redundancy_cost: Optional[float],
) -> None:
    models = {
        "primary": llm.config.model if llm is not None else None,
        "redundancy": "openai/gpt-5-pro",
    }
    token_totals = {
        "primary": llm.get_total_tokens() if llm is not None else 0,
        "redundancy": int(redundancy_tokens),
    }
    cost_totals = {
        "primary": llm.get_total_cost_usd() if llm is not None else None,
        "redundancy": redundancy_cost,
    }
    write_run_meta(
        run_ctx=run_ctx,
        args=args,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        error=error,
        models=models,
        token_totals=token_totals,
        cost_totals_usd=cost_totals,
    )


def _known_ids_from_kb(kb: Optional[KnowledgeBase]) -> Tuple[set[str], set[str]]:
    if kb is None:
        return set(), set()
    cite_keys: set[str] = set()
    rids: set[str] = set()
    for chunk in getattr(kb, "chunks", []):
        cite_key = getattr(chunk, "cite_key", "") or kb_cite_key(chunk.source_path, chunk.loc)
        rid = getattr(chunk, "rid", None)
        if cite_key:
            cite_keys.add(str(cite_key))
        if rid:
            rids.add(str(rid))
    return cite_keys, rids


def run_book(args: Any, run_ctx: Optional[RunContext], logger: Any) -> int:
    started_at = datetime.now(timezone.utc)
    status = "ok"
    error: Optional[str] = None
    redundancy_tokens = 0
    redundancy_cost: Optional[float] = None
    llm: Optional[OpenRouterLLM] = None

    try:
        input_path = Path(args.input).expanduser().resolve()
        out_dir = Path(args.out_dir).expanduser().resolve()
        json_path = Path(args.json_path).expanduser()
        if not json_path.is_absolute():
            json_path = out_dir / json_path
        json_path = json_path.resolve()

        use_legacy_tex = bool(getattr(args, "legacy_tex", False))
        content_format = "latex" if use_legacy_tex else "markdown"
        prompts = _apply_prompt_overrides(load_book_prompts(content_format=content_format))
        set_prompt_registry("book", prompts)

        if run_ctx is None:
            run_ctx = RunContext.create(out_dir=out_dir, mode="book")

        progress_path = run_ctx.structure_graph_path

        if not input_path.exists():
            print(f"Chyba: vstupní soubor neexistuje: {input_path}", file=sys.stderr)
            return 2
        input_sha256 = _file_sha256(input_path)

        out_dir.mkdir(parents=True, exist_ok=True)
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # Optional Knowledge Base
        t0 = time.perf_counter()
        kb = None
        if args.kb_dir:
            kb_dir = Path(args.kb_dir).expanduser().resolve()
            print(f"[KB] Buduji/načítám znalostní databázi z: {kb_dir}")
            kb = KnowledgeBase.build_from_directory(
                kb_dir,
                cache_dir=out_dir / ".kb_cache",
                force_rebuild=bool(args.rebuild_kb),
            )
            print(f"[KB] Hotovo. Počet chunků: {len(kb.chunks)}")
            kb_index = build_kb_index(kb)
            (out_dir / "kb_sources.json").write_text(
                json.dumps(kb_index, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            print("[KB] --kb-dir nebyl zadán. RAG bude vypnut.")
        print(f"[KB] Trvání: {_format_duration(time.perf_counter() - t0)}")

        llm = OpenRouterLLM()
        # Parametry kurzu z UI (jestliže jsou) — vkládají se do osnovy pro tvorbu
        # struktury i do atributů grafu jako kontext pro psaní sekcí.
        ui_params = {}
        try:
            _raw = os.environ.get("AUTOGENBOOK_UI_PARAMS", "").strip()
            if _raw:
                _loaded = json.loads(_raw)
                if isinstance(_loaded, dict):
                    ui_params = _loaded
        except Exception:
            ui_params = {}

        def _apply_ui_params(spec_text: str) -> str:
            if not ui_params:
                return spec_text
            lines = []
            for key, label in (
                ("suggested_title", "Název"),
                ("target_audience", "Cílová skupina"),
                ("tone_of_voice", "Tón textu"),
                ("output_purpose", "Účel výstupu"),
            ):
                val = str(ui_params.get(key) or "").strip()
                if val:
                    lines.append(f"- {label}: {val}")
            depth = ui_params.get("recommended_depth")
            if depth not in (None, ""):
                lines.append(f"- Doporučená hloubka členění: {depth}")
            if not lines:
                return spec_text
            return (spec_text or "").rstrip() + "\n\n# Dodatečné požadavky (autoGenBook UI)\n" + "\n".join(lines) + "\n"

        def _inject_ui_params_into_graph(g: Any) -> None:
            if not ui_params:
                return
            if str(ui_params.get("target_audience") or "").strip():
                g.graph["target_readers"] = str(ui_params["target_audience"]).strip()
            extra_bits = []
            if str(ui_params.get("tone_of_voice") or "").strip():
                extra_bits.append(f"Tón textu: {ui_params['tone_of_voice'].strip()}")
            if str(ui_params.get("output_purpose") or "").strip():
                extra_bits.append(f"Účel výstupu: {ui_params['output_purpose'].strip()}")
            if extra_bits:
                current = str(g.graph.get("additional_requirements") or "").strip()
                g.graph["additional_requirements"] = (current + "\n" + "\n".join(extra_bits)).strip()
            try:
                depth = int(ui_params.get("recommended_depth"))
                if depth:
                    g.graph["max_depth"] = depth
            except (TypeError, ValueError):
                pass
            save_graph_json(g, progress_path)

        retrieval_manager = RetrievalManager(local_kb=kb, default_k=6, max_chars_total=6000)
        if getattr(args, "enable_web_rag", False):
            mcp_papers = MCPPaperRetriever()
            api_key = os.environ.get("TAVILY_API_KEY")
            tavily = TavilyRetriever(api_key=api_key)
            retrieval_manager = RetrievalManager(
                local_kb=kb,
                mcp_papers=mcp_papers,
                tavily=tavily,
                enable_web=True,
                default_k=6,
                max_chars_total=6000,
            )
            has_mcp = bool(mcp_papers and mcp_papers.is_available())
            has_tavily = bool(tavily and tavily.api_key)
            if not has_mcp and not has_tavily:
                print(
                    "[WARN] Web RAG enabled but no MCP paper tools or Tavily API key available; using KB only."
                )
            elif not has_mcp and has_tavily:
                print("[INFO] MCP paper tools unavailable; falling back to Tavily search.")

        # Decide TXT vs JSON / Resume
        g = None
        force_txt_regen = False
        if args.resume and progress_path.exists():
            print(f"[RESUME] Načítám uloženou strukturu z: {progress_path}")
            loaded_graph = load_graph_json(progress_path)
            resume_allowed = True
            resume_reason = ""

            graph_input = _resolve_input_path(loaded_graph.graph.get("input_path"))
            if graph_input is not None and graph_input != input_path:
                resume_allowed = False
                resume_reason = (
                    "V ulozene strukture je jiny vstupni soubor: "
                    f"{graph_input} (aktualni: {input_path})."
                )
            graph_input_sha256 = str(loaded_graph.graph.get("input_sha256", "")).strip()
            if resume_allowed and graph_input_sha256:
                if graph_input_sha256 != input_sha256:
                    resume_allowed = False
                    resume_reason = (
                        "Vstupni soubor byl zmenen od posledniho behu "
                        f"(ulozeny hash: {graph_input_sha256[:12]}..., aktualni: {input_sha256[:12]}...)."
                    )
            elif resume_allowed:
                resume_allowed = False
                resume_reason = (
                    "Ulozena struktura neobsahuje hash vstupu (starsi format); "
                    "pro bezpecnost vytvarim novy beh z aktualniho --input."
                )

            if resume_allowed:
                prev_meta_path = out_dir / "run_meta.json"
                if prev_meta_path.exists():
                    try:
                        prev_meta = json.loads(prev_meta_path.read_text(encoding="utf-8"))
                        prev_mode = str(prev_meta.get("mode", "")).strip().lower()
                        prev_input = _resolve_input_path((prev_meta.get("args") or {}).get("input"))
                        if prev_mode and prev_mode != "book":
                            resume_allowed = False
                            resume_reason = (
                                f"Predchozi run_meta je pro mode '{prev_mode}', ne pro 'book'."
                            )
                        elif prev_input is not None and prev_input != input_path:
                            resume_allowed = False
                            resume_reason = (
                                "Predchozi run_meta obsahuje jiny vstupni soubor: "
                                f"{prev_input} (aktualni: {input_path})."
                            )
                    except Exception:
                        pass

            if resume_allowed:
                g = loaded_graph
            else:
                print(f"[RESUME] Preskakuji --resume: {resume_reason}")
                print("[RESUME] Pokracuji novym behom z aktualniho --input.")
                force_txt_regen = True
        if g is None:
            t0 = time.perf_counter()
            book_json = None
            if json_path.exists():
                if force_txt_regen and not args.use_json:
                    print("[JSON] Ignoruji existujici JSON a generuji novy z TXT.")
                    choice = "t"
                elif args.use_txt:
                    choice = "t"
                elif args.use_json:
                    choice = "j"
                else:
                    choice = _ask_choice(
                        f"JSON soubor už existuje ({json_path.name}). Použít existující JSON, nebo znovu vygenerovat z TXT?",
                        {"j": "json", "t": "txt"},
                        default="j",
                    )
                if choice == "j":
                    book_json = json.loads(_read_text(json_path))
                else:
                    txt_spec = _apply_ui_params(_read_text(input_path))
                    book_json = generate_book_json_from_txt(llm, txt_spec, kb=kb)
                    usage = llm.get_last_usage()
                    if usage:
                        log_usage(out_dir, "book_json", llm, usage, {"stage": "book_json"})
                    revised, redundancy_tokens, redundancy_cost = _revise_book_json_for_redundancy(
                        book_json,
                        out_dir,
                    )
                    if revised is not None:
                        print("[JSON] Navržená revize struktury (kontrola redundance):")
                        print(json.dumps(revised, ensure_ascii=False, indent=2))
                        if _ask_yes_no("Nahradit původní JSON touto revizí?", default="n"):
                            book_json = revised
                        else:
                            revised_path = json_path.with_name(json_path.stem + "_revised.json")
                            revised_path.write_text(
                                json.dumps(revised, ensure_ascii=False, indent=2), encoding="utf-8"
                            )
                            print(f"[JSON] Revize uložena do: {revised_path}")
                    json_path.write_text(json.dumps(book_json, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                txt_spec = _apply_ui_params(_read_text(input_path))
                book_json = generate_book_json_from_txt(llm, txt_spec, kb=kb)
                usage = llm.get_last_usage()
                if usage:
                    log_usage(out_dir, "book_json", llm, usage, {"stage": "book_json"})
                revised, redundancy_tokens, redundancy_cost = _revise_book_json_for_redundancy(
                    book_json,
                    out_dir,
                )
                if revised is not None:
                    print("[JSON] Navržená revize struktury (kontrola redundance):")
                    print(json.dumps(revised, ensure_ascii=False, indent=2))
                    if _ask_yes_no("Nahradit původní JSON touto revizí?", default="n"):
                        book_json = revised
                    else:
                        revised_path = json_path.with_name(json_path.stem + "_revised.json")
                        revised_path.write_text(
                            json.dumps(revised, ensure_ascii=False, indent=2), encoding="utf-8"
                        )
                        print(f"[JSON] Revize uložena do: {revised_path}")
                json_path.write_text(json.dumps(book_json, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[JSON] Trvani: {_format_duration(time.perf_counter() - t0)}")

            # Build graph and subdivide
            t0 = time.perf_counter()
            g = build_graph_from_book_json(book_json)
            g.graph["input_path"] = str(input_path)
            g.graph["input_sha256"] = input_sha256
            subdivide_graph(
                llm,
                g,
                kb=kb,
                rag_top_k=6,
                rag_max_chars_total=6000,
                retrieval_manager=retrieval_manager,
                progress_path=progress_path,
            )
            print(f"[SUBDIVIDE] Trvani: {_format_duration(time.perf_counter() - t0)}")

            # Save structure snapshot
            save_graph_json(g, progress_path)

        if g is None:
            raise RuntimeError("Graph not initialized.")
        if not str(g.graph.get("input_path", "")).strip():
            g.graph["input_path"] = str(input_path)
        if not str(g.graph.get("input_sha256", "")).strip():
            g.graph["input_sha256"] = input_sha256
        save_graph_json(g, progress_path)
        _inject_ui_params_into_graph(g)

        author = str(g.graph.get("author", "") or "").strip()
        if not author:
            author = _ask_text("Zadejte autora knihy", required=True)
            g.graph["author"] = author
            save_graph_json(g, progress_path)

        single_node = str(getattr(args, "single_node", "") or "").strip() or None
        # Per-node konfigurace z UI (custom prompt, prioritní KB soubory, stávající text)
        _node_params = _load_json_env("AUTOGENBOOK_NODE_PARAMS") or {}
        node_config: Dict[str, Any] = _node_params if isinstance(_node_params, dict) else {}
        if getattr(args, "outline_only", False) and not single_node:
            print("[OUTLINE] Režim outline_only — struktura vygenerována, sekce se nepíší.")
            print(json.dumps({"structure_written": str(json_path), "graph_written": str(progress_path)}, ensure_ascii=False, indent=2))
            return 0

        # Generate section contents
        export_tex = bool(getattr(args, "export_tex", False))
        tex_output = not args.no_tex
        pdf_output = not args.no_pdf
        md_output = not args.no_md
        if content_format == "markdown":
            tex_output = export_tex and tex_output
            pdf_output = export_tex and pdf_output
        cfg = AppConfig(
            content_format=content_format,
            tex_output=tex_output,
            pdf_output=pdf_output,
            md_output=md_output,
            equation_frequency_level=int(g.graph.get("equation_frequency_level", 4)),
            do_consider_outline=bool(g.graph.get("do_consider_outline", True)),
            do_consider_previous_sections=bool(g.graph.get("do_consider_previous_sections", True)),
            n_previous_sections=1 if bool(g.graph.get("do_consider_previous_sections", True)) else 0,
        )

        print("[GEN] Generuji obsah sekcí|")
        t0 = time.perf_counter()
        generate_contents(
            llm,
            g,
            out_dir=out_dir,
            kb=kb,
            cfg=cfg,
            retrieval_manager=retrieval_manager,
            progress_path=progress_path,
            resume=bool(args.resume),
            only_key=single_node,
            node_config=node_config,
        )
        if single_node:
            print(f"[SINGLE_NODE] Vygenerována pouze sekce {single_node}.")
            return 0
        print(f"[GEN] Trvani: {_format_duration(time.perf_counter() - t0)}")

        outputs = []
        md_first = content_format == "markdown"
        md_path = None
        tex_path = None

        if cfg.md_output and md_first:
            print("[GEN] Sestavuji Markdown dokument|")
            t0 = time.perf_counter()
            md_path = build_markdown_document(g, out_dir=out_dir)
            print(f"[MD] Trvani: {_format_duration(time.perf_counter() - t0)}")
            outputs.append(md_path)

        if cfg.tex_output or cfg.pdf_output:
            print("[GEN] Sestavuji LaTeX dokumenty|")
            t0 = time.perf_counter()
            try:
                tex_path = build_latex_document(g, out_dir=out_dir, kb=kb)
            except Exception as exc:
                if md_first and not use_legacy_tex:
                    print(f"[WARN] Markdown->LaTeX failed: {exc}")
                    print("[INFO] Falling back to legacy LaTeX generation.")
                    legacy_prompts = load_book_prompts(content_format="latex")
                    set_prompt_registry("book", legacy_prompts)
                    legacy_cfg = AppConfig(
                        content_format="latex",
                        tex_output=True,
                        pdf_output=cfg.pdf_output,
                        md_output=cfg.md_output,
                        equation_frequency_level=int(g.graph.get("equation_frequency_level", 4)),
                        do_consider_outline=bool(g.graph.get("do_consider_outline", True)),
                        do_consider_previous_sections=bool(g.graph.get("do_consider_previous_sections", True)),
                        n_previous_sections=1 if bool(g.graph.get("do_consider_previous_sections", True)) else 0,
                    )
                    generate_contents(
                        llm,
                        g,
                        out_dir=out_dir,
                        kb=kb,
                        cfg=legacy_cfg,
                        retrieval_manager=retrieval_manager,
                        progress_path=progress_path,
                        resume=bool(args.resume),
                    )
                    tex_path = build_latex_document(g, out_dir=out_dir, kb=kb)
                    md_first = False
                else:
                    raise
            print(f"[LATEX] Trvani: {_format_duration(time.perf_counter() - t0)}")

            if tex_path is not None and cfg.tex_output:
                outputs.append(tex_path)

            audit_book = bool(getattr(args, "audit_book", False))
            audit_mode = str(getattr(args, "audit_book_mode", "warn") or "warn")
            if audit_mode == "off":
                audit_book = False
            if audit_book and tex_path is not None:
                tex_text = tex_path.read_text(encoding="utf-8", errors="ignore")
                known_cite_keys, known_rids = _known_ids_from_kb(kb)
                report = audit_latex(
                    tex_path=tex_path,
                    tex_text=tex_text,
                    doc_kind="book",
                    known_cite_keys=known_cite_keys,
                    known_rids=known_rids,
                    project_root=Path.cwd(),
                    config=AuditorConfig(
                        enabled=True,
                        mode=audit_mode,
                        check_numeric_claims=False,
                    ),
                )
                report.dump(out_dir / "audit_report.json")
                if (
                    audit_mode == "strict"
                    and report.counts_by_severity.get(AuditSeverity.ERROR.value, 0) > 0
                ):
                    status = "error"
                    error = "Book audit failed in strict mode. See audit_report.json for details."
                    return 4

            if cfg.pdf_output and tex_path is not None:
                print("[GEN] Kompiluji PDF (pdflatex)|")
                t0 = time.perf_counter()
                pdf_path = compile_pdf(tex_path)
                print(f"[PDF] Trvani: {_format_duration(time.perf_counter() - t0)}")
                outputs.append(pdf_path)

            if cfg.md_output and not md_first and tex_path is not None:
                print("[GEN] Exportuji Markdown|")
                t0 = time.perf_counter()
                md_path = export_markdown(tex_path)
                print(f"[MD] Trvani: {_format_duration(time.perf_counter() - t0)}")
                outputs.append(md_path)

        print("\nHotovo. Výstupy:")
        for p in outputs:
            print(f" - {p}")
        print(f"[TOKENS] Celkem spotřebováno tokenů: {llm.get_total_tokens()}")
        total_cost = llm.get_total_cost_usd()
        if total_cost is not None:
            print(f"[COST] Celková cena: ${total_cost:.6f}")

        return 0
    except Exception as exc:
        status = "error"
        error = str(exc)
        raise
    finally:
        finished_at = datetime.now(timezone.utc)
        if run_ctx is not None:
            _write_run_meta(
                run_ctx=run_ctx,
                args=args,
                started_at=started_at,
                finished_at=finished_at,
                status=status,
                error=error,
                llm=llm,
                redundancy_tokens=redundancy_tokens,
                redundancy_cost=redundancy_cost,
            )
