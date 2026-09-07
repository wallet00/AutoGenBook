"""AutoGenBook Web UI — FastAPI application and API routes."""
from __future__ import annotations

import json
import os
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from openrouter_llm import OpenRouterLLM

from .runner import RunError, load_env_file, resolve_tavily_key, runner, save_tavily_key

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = REPO_ROOT / "projects"
try:
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    os.chmod(PROJECTS_ROOT, 0o777)  # best-effort: pomáhá, když je volume root zapisovatelný appuserem
except PermissionError:
    import sys as _sys
    print(
        "[WARN] Nemohu zapisovat do %s. Zkontrolujte vlastníka PVC/fsGroup "
        "(ne-root uživatel musí mít právo zápisu)." % PROJECTS_ROOT,
        file=_sys.stderr,
    )

UI_DIR = Path(__file__).parent
app = FastAPI(title="AutoGenBook UI", version="0.1.0")
app.mount("/static", StaticFiles(directory=str(UI_DIR / "static")), name="static")

# ── Jednoduchá autentizace sdíleným heslem ────────────────────────
# Zapne se jen když je nastaveno AUTOGENBOOK_UI_PASSWORD.
# Kdo zná heslo, dostane se dovnitř (session cookie po dobu SESSION_TTL).
AUTH_PASSWORD = os.environ.get("AUTOGENBOOK_UI_PASSWORD", "").strip()
SESSION_COOKIE = "autogenbook_session"
_sessions: dict[str, float] = {}  # token -> expirace (unix ts)
SESSION_TTL = 12 * 3600  # 12 h


def _auth_enabled() -> bool:
    return bool(AUTH_PASSWORD)


@app.middleware("http")
async def _auth_middleware(request: Request, call_next):
    if not _auth_enabled():
        return await call_next(request)
    path = request.url.path
    if path == "/login" or path.startswith("/static/"):
        return await call_next(request)
    token = request.cookies.get(SESSION_COOKIE, "")
    ok = token in _sessions and _sessions[token] > time.time()
    if not ok:
        if path.startswith("/api/") or path.startswith("/files"):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return RedirectResponse("/login", status_code=303)
    return await call_next(request)


@app.get("/login", response_class=HTMLResponse)
def login_page(error: bool = False):
    if not _auth_enabled():
        return RedirectResponse("/", status_code=303)
    html = (UI_DIR / "templates" / "login.html").read_text(encoding="utf-8")
    return html.replace("{{error_style}}", "display:block" if error else "display:none")


@app.post("/login")
async def login_post(request: Request):
    if not _auth_enabled():
        return RedirectResponse("/", status_code=303)
    form = await request.form()
    if form.get("password") == AUTH_PASSWORD:
        token = secrets.token_hex(32)
        _sessions[token] = time.time() + SESSION_TTL
        resp = RedirectResponse("/", status_code=303)
        resp.set_cookie(
            SESSION_COOKIE, token, httponly=True, samesite="lax",
            max_age=SESSION_TTL, secure=request.url.scheme == "https",
        )
        return resp
    return RedirectResponse("/login?error=1", status_code=303)


@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE, "")
    _sessions.pop(token, None)
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

DEFAULT_SPEC = """Název: NÁZEV PŘEDMĚTU
Obsah: Stručný popis předmětu a cíl.
Kapitoly:
## KAPITOLA 1: ÚVOD

### 1.1 Název sekce
**Obsah:**
- bod

**Zdroje:**
- https://...
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "project"


def project_paths(pid: str) -> Path:
    return PROJECTS_ROOT / pid


def _read_meta(pid: str) -> dict:
    meta_path = project_paths(pid) / "project.json"
    if not meta_path.exists():
        raise HTTPException(404, "Projekt neexistuje")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _write_meta(pid: str, meta: dict) -> None:
    project_paths(pid).mkdir(parents=True, exist_ok=True)
    try:
        (project_paths(pid) / "project.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except PermissionError as e:
        raise HTTPException(
            500,
            "Nemohu uložit projekt (přístup odepřen, uid=%d). Soubory na PVC jsou nejspíš "
            "vlastněné jiným uživatelem (dříve root). Opravte vlastnictví/PVC nebo použijte "
            "storage s podporou fsGroup=2000." % (os.getuid() if hasattr(os, "getuid") else -1),
        ) from e


def _load_dotenv_for_config() -> dict:
    from .runner import load_env_file

    return load_env_file(REPO_ROOT / ".env")


# ── Pages ──────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def index_page():
    return (UI_DIR / "templates" / "index.html").read_text(encoding="utf-8")


# ── Config ─────────────────────────────────────────────────────────
@app.get("/api/config")
def api_config():
    import os

    env = _load_dotenv_for_config()
    # V Dockeru přicházejí proměnné přes env_file (do os.environ); .env je jen záloža.
    base_url = os.environ.get("AUTOGENBOOK_LLM_BASE_URL") or env.get("AUTOGENBOOK_LLM_BASE_URL", "")
    model = os.environ.get("AUTOGENBOOK_LLM_MODEL") or env.get("AUTOGENBOOK_LLM_MODEL", "openai/gpt-5-mini")
    has_key = bool(
        os.environ.get("AUTOGENBOOK_LLM_API_KEY")
        or env.get("AUTOGENBOOK_LLM_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or env.get("OPENROUTER_API_KEY")
    )
    return {"base_url": base_url, "model": model, "has_key": has_key, "auth": _auth_enabled()}


# ── Projects ───────────────────────────────────────────────────────
@app.get("/api/projects")
def list_projects():
    out = []
    for p in sorted(PROJECTS_ROOT.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        meta_path = p / "project.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        state = runner.status(meta["id"])
        meta["run_status"] = state["status"]
        out.append(meta)
    return out


@app.post("/api/projects")
def create_project(payload: dict):
    name = (payload.get("name") or "").strip() or "bez-nazvu"
    lang = payload.get("language") or "cs"
    pid = f"{_slug(name)}-{secrets.token_hex(2)}"
    meta = {
        "id": pid,
        "name": name,
        "language": lang,
        "created": _now(),
        "updated": _now(),
        "spec": payload.get("spec") or DEFAULT_SPEC,
    }
    p = project_paths(pid)
    p.mkdir(parents=True, exist_ok=True)
    (p / "kb").mkdir(exist_ok=True)
    (p / "output").mkdir(exist_ok=True)
    (p / "spec.txt").write_text(meta["spec"], encoding="utf-8")
    _write_meta(pid, meta)
    return meta


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    meta = _read_meta(pid)
    meta["run_status"] = runner.status(pid)["status"]
    return meta


@app.put("/api/projects/{pid}/spec")
def save_spec(pid: str, payload: dict):
    meta = _read_meta(pid)
    spec = payload.get("spec")
    if spec is not None:
        meta["spec"] = spec
        (project_paths(pid) / "spec.txt").write_text(spec, encoding="utf-8")
    if payload.get("language"):
        meta["language"] = payload["language"]
    meta["updated"] = _now()
    _write_meta(pid, meta)
    return meta


# ── Knowledge base (materiály) ─────────────────────────────────────
def _kb_files(pid: str):
    kb = project_paths(pid) / "kb"
    kb.mkdir(exist_ok=True)
    files = []
    for f in sorted(kb.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            files.append({"name": f.name, "size": f.stat().st_size})
    return files


@app.get("/api/projects/{pid}/kb")
def list_kb(pid: str):
    _read_meta(pid)
    return _kb_files(pid)


@app.post("/api/projects/{pid}/kb")
async def upload_kb(pid: str, file: UploadFile = File(...)):
    _read_meta(pid)
    kb = project_paths(pid) / "kb"
    kb.mkdir(exist_ok=True)
    name = file.filename.replace("/", "_").replace("\\", "_")
    dest = kb / name
    data = await file.read()
    dest.write_bytes(data)
    return {"name": name, "size": len(data)}


@app.delete("/api/projects/{pid}/kb/{filename}")
def delete_kb(pid: str, filename: str):
    _read_meta(pid)
    dest = project_paths(pid) / "kb" / filename
    if dest.exists() and dest.is_file():
        dest.unlink()
    return {"ok": True}


# ── Analysis (Setup Assistant) ────────────────────────────────────
ANALYSIS_FIELDS = ("suggested_title", "target_audience", "tone_of_voice", "output_purpose", "recommended_depth", "language")


@app.post("/api/projects/{pid}/analyze-spec")
def analyze_spec(pid: str):
    meta = _read_meta(pid)
    p = project_paths(pid)
    spec_path = p / "spec.txt"
    spec = (spec_path.read_text(encoding="utf-8", errors="ignore") if spec_path.exists() else meta.get("spec", "") or "").strip()[:12000]

    kb_context = ""
    kb = p / "kb"
    if kb.exists():
        took = 0
        for f in sorted(kb.iterdir()):
            if took >= 3:
                break
            if f.is_file() and f.suffix.lower() in (".txt", ".md", ".csv", ".json", ".html", ""):
                try:
                    t = f.read_text(encoding="utf-8", errors="ignore")[:6000]
                    kb_context += f"\n--- {f.name} ---\n{t}\n"
                    took += 1
                except Exception:
                    pass
    llm = OpenRouterLLM()
    sys = (
        "Jsi asistent pro přípravu výukových materiálů. Z dané osnovy / sylabu a materiálů kurzu "
        "navrhni parametry pro generování učebnice. Odpověz VÝHRADNĚ validním JSON objektem s klíči: "
        "suggested_title (string), target_audience (string, 15-40 slov, např. \"Studenti informatiky a Service Designu na FI MUNI\"), "
        "tone_of_voice (string, krátký popis stylu, např. \"Akademický výkladový text s IT/SaaS příklady\"), "
        "output_purpose (string, např. \"Textbook / Podklad pro NotebookLM\"), "
        "language (string, JAZYK generovaných podkladů — např. \"English\" / \"Čeština\"; pokud osnova nic neříká, dej \"English\"), "
        "recommended_depth (integer 2-5). Bez žádného textu mimo JSON."
    )
    user = f"OSNOVA / SYLABUS:\n{spec}\n"
    if kb_context:
        user += f"\nMATERIÁLY (znalostní báze):\n{kb_context}\n"
    try:
        res = llm.chat_json([{"role": "system", "content": sys}, {"role": "user", "content": user}])
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Analýza osnovy selhala: {e}")
    if isinstance(res, dict):
        result = res
    elif isinstance(res, list) and res and isinstance(res[0], dict):
        result = res[0]
    else:
        result = {}
    try:
        depth = int(result.get("recommended_depth") or 3)
    except (TypeError, ValueError):
        depth = 3
    suggested = {
        "suggested_title": str(result.get("suggested_title") or "").strip()[:200],
        "target_audience": str(result.get("target_audience") or "").strip()[:300],
        "tone_of_voice": str(result.get("tone_of_voice") or "").strip()[:300],
        "output_purpose": str(result.get("output_purpose") or "").strip()[:200],
        "recommended_depth": max(2, min(5, depth)),
        "language": str(result.get("language") or "").strip()[:60] or "English",
    }
    meta["analysis"] = suggested
    meta["updated"] = _now()
    _write_meta(pid, meta)
    return suggested


@app.put("/api/projects/{pid}/analysis")
def save_analysis(pid: str, payload: dict):
    meta = _read_meta(pid)
    cur = dict(meta.get("analysis") or {})
    for key in ANALYSIS_FIELDS:
        if key in payload:
            cur[key] = payload[key]
    meta["analysis"] = cur
    meta["updated"] = _now()
    _write_meta(pid, meta)
    return {"ok": True, "analysis": cur}


# ── Run ────────────────────────────────────────────────────────────
def _analysis_params(meta: dict) -> dict:
    return meta.get("analysis") or {}


def _node_env(pid: str, cfg: dict) -> dict:
    """Per-node parametry pro single_node/branch běh (gen_mode, vlastní prompt, prioritní KB, stávající text)."""
    mode = cfg.get("mode") or "book"
    if mode not in ("single_node", "branch"):
        return {}
    node: dict = {}
    gen_mode = str(cfg.get("gen_mode") or "").strip()
    if gen_mode not in ("full", "enrich"):
        gen_mode = "enrich" if bool(cfg.get("include_existing")) else "full"
    node["gen_mode"] = gen_mode
    if gen_mode == "enrich" or bool(cfg.get("include_existing")):
        node["include_existing"] = True
    custom = str(cfg.get("custom_prompt") or "").strip()
    if custom:
        node["custom_prompt"] = custom
    kb_list = [str(x) for x in (cfg.get("kb_files") or []) if str(x).strip()]
    if kb_list:
        node["kb_files"] = kb_list
    if bool(cfg.get("include_child_texts")):
        node["include_child_texts"] = True
    return {"AUTOGENBOOK_NODE_PARAMS": json.dumps(node, ensure_ascii=False)}


def _prompt_env(pid: str) -> dict:
    """Projektové překryvy promptů (project.json["prompts"]) předané do běhu."""
    meta = _read_meta(pid)
    ovr = meta.get("prompts") or {}
    if not isinstance(ovr, dict) or not ovr:
        return {}
    clean = {k: v for k, v in ovr.items() if isinstance(v, str) and v.strip()}
    if not clean:
        return {}
    return {"AUTOGENBOOK_PROMPT_OVERRIDES": json.dumps(clean, ensure_ascii=False)}


def _build_argv(pid: str, cfg: dict) -> list[str]:
    p = project_paths(pid)
    out = p / "output"
    kb = p / "kb"
    spec = p / "spec.txt"
    mode = (cfg.get("mode") or "book") or "book"
    cli_mode = "book" if mode in ("outline_only", "single_node", "branch") else mode

    argv = [
        "python",
        str(REPO_ROOT / "main.py"),
        "--mode", cli_mode,
        "--input", str(spec),
        "--out-dir", str(out),
    ]
    kb_files = [f for f in kb.iterdir() if f.is_file() and not f.name.startswith(".")] if kb.exists() else []
    if kb_files:
        argv += ["--kb-dir", str(kb)]

    if mode == "outline_only":
        argv += ["--outline-only", "--use-txt"]
        return argv

    if mode == "single_node":
        node_key = str(cfg.get("node_id") or "").strip().replace(".", "-")
        if not node_key:
            raise RunError("single_node vyžaduje node_id")
        argv += ["--single-node", node_key, "--resume", "--no-md", "--no-tex", "--no-pdf"]
        if cfg.get("enable_web_rag"):
            argv += ["--enable-web-rag"]
        return argv

    if mode == "branch":
        bkey = str(cfg.get("node_id") or "").strip().replace(".", "-")
        if not bkey:
            raise RunError("branch vyžaduje node_id")
        # Necháme sestavit .md (bez tex/pdf), aby se promítly změny do finálního dokumentu.
        argv += ["--branch-root", bkey, "--resume", "--no-tex", "--no-pdf"]
        if cfg.get("enable_web_rag"):
            argv += ["--enable-web-rag"]
        return argv

    if cfg.get("enable_web_rag"):
        argv += ["--enable-web-rag"]
    audit = cfg.get("audit_mode")
    if audit in ("warn", "strict"):
        argv += ["--audit-book", "--audit-book-mode", audit]
    if cfg.get("export_tex"):
        argv += ["--export-tex"]
    argv += ["--no-pdf"] if not cfg.get("pdf") else []
    return argv


@app.post("/api/projects/{pid}/run")
def start_run(pid: str, payload: dict):
    _read_meta(pid)
    try:
        argv = _build_argv(pid, payload)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, str(e))
    extra_env = {}
    if payload.get("model"):
        extra_env["AUTOGENBOOK_LLM_MODEL"] = payload["model"]
    analysis = _analysis_params(_read_meta(pid))
    if analysis:
        extra_env["AUTOGENBOOK_UI_PARAMS"] = json.dumps(analysis, ensure_ascii=False)
    extra_env.update(_node_env(pid, payload))
    extra_env.update(_prompt_env(pid))
    try:
        state = runner.start({"id": pid, "path": project_paths(pid)}, argv, extra_env)
    except RunError as e:
        raise HTTPException(409, str(e))
    return state


@app.post("/api/projects/{pid}/cancel")
def cancel_run(pid: str):
    return {"ok": runner.cancel(pid)}


@app.post("/api/projects/{pid}/pause")
def pause_run(pid: str):
    return {"ok": runner.pause(pid)}


@app.post("/api/projects/{pid}/resume")
def resume_run(pid: str):
    return {"ok": runner.resume(pid)}


@app.get("/api/projects/{pid}/status")
def run_status(pid: str):
    return runner.status(pid)


@app.get("/api/projects/{pid}/events")
def run_events(pid: str):
    _read_meta(pid)
    log_path = project_paths(pid) / "run.log"
    return StreamingResponse(
        runner.tail(pid, log_path),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/projects/{pid}/log")
def get_run_log(pid: str):
    _read_meta(pid)
    log_path = project_paths(pid) / "run.log"
    if not log_path.exists():
        raise HTTPException(404, "Log zatím neexistuje")
    return HTMLResponse(f"<pre>{log_path.read_text(encoding='utf-8', errors='replace')}</pre>")


# ── Output ─────────────────────────────────────────────────────────
def _iter_output(pid: str):
    out = project_paths(pid) / "output"
    if not out.exists():
        return []
    items = []
    for f in sorted(out.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            rel = f.relative_to(out)
            items.append({"path": str(rel), "size": f.stat().st_size})
    return items


@app.get("/api/projects/{pid}/output")
def list_output(pid: str):
    _read_meta(pid)
    return _iter_output(pid)


@app.get("/api/projects/{pid}/output/file")
def read_output(pid: str, path: str):
    _read_meta(pid)
    base = (project_paths(pid) / "output").resolve()
    target = (base / path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(400, "Neplatná cesta")
    if not target.is_file():
        raise HTTPException(404, "Soubor neexistuje")
    suffix = target.suffix.lower()
    if suffix in (".md", ".txt", ".json", ".tex", ".log"):
        return HTMLResponse(f"<pre>{target.read_text(encoding='utf-8', errors='replace')}</pre>")
    return FileResponse(target, filename=target.name)


@app.get("/api/projects/{pid}/download/{name}")
def download_output(pid: str, name: str):
    _read_meta(pid)
    base = (project_paths(pid) / "output").resolve()
    target = (base / name).resolve()
    if not str(target).startswith(str(base)) or not target.is_file():
        raise HTTPException(404, "Soubor neexistuje")
    return FileResponse(target, filename=target.name)


# ── Structure (strom kapitol) ─────────────────────────────────────
@app.get("/api/projects/{pid}/structure")
def get_structure(pid: str):
    _read_meta(pid)
    out = project_paths(pid) / "output"
    graph_path = out / "structure_graph.json"
    fallback = out / "book_structure.json"
    nodes: dict = {}
    edges: list = []
    has_graph = False

    if graph_path.exists():
        try:
            data = json.loads(graph_path.read_text(encoding="utf-8"))
            nodes = data.get("nodes") or {}
            edges = data.get("edges") or []
            has_graph = True
        except Exception:
            nodes, edges = {}, []
    if not has_graph and fallback.exists():
        try:
            data = json.loads(fallback.read_text(encoding="utf-8"))
            nodes = {"book": {"title": data.get("title", "")}}
            edges = []

            def _walk(d: dict, parent: str, prefix: str) -> None:
                key = prefix
                node = dict(d)
                node.pop("childs", None)
                nodes[key] = node
                edges.append([parent, key])
                for i, ch in enumerate(d.get("childs") or [], 1):
                    ck = str(i) if prefix == "book" else f"{prefix}-{i}"
                    _walk(ch, key, ck)

            for i, ch in enumerate(data.get("childs") or [], 1):
                _walk(ch, "book", str(i))
            has_graph = True
        except Exception:
            nodes, edges = {}, []

    sections_dir = out / "sections"
    sec: dict = {}
    if sections_dir.exists():
        for f in sections_dir.iterdir():
            if f.suffix == ".md" and f.is_file():
                sec[f.stem] = {"exists": True, "size": f.stat().st_size, "mtime": float(f.stat().st_mtime)}

    children: dict = {}
    for pair in edges:
        children.setdefault(pair[0], []).append(pair[1])

    def _build(key: str) -> dict:
        nd = nodes.get(key) or {}
        return {
            "id": key,
            "title": str(nd.get("title") or "").strip(),
            "summary": str(nd.get("summary") or "").strip(),
            "children": [_build(c) for c in children.get(key, [])],
            "leaf": not (children.get(key) or []),
            "locked": bool(nd.get("locked")),
            "manual": bool(nd.get("manual_override")),
            **sec.get(key, {"exists": False, "size": 0, "mtime": 0}),
        }

    roots = children.get("book", []) or [
        k for k in nodes if k != "book" and not any(e[1] == k for e in edges)
    ]
    tree = [_build(r) for r in roots]
    total = max(0, len(nodes) - 1)
    generated = sum(1 for k in sec if k in nodes)
    return {"tree": tree, "generated": generated, "total": total, "has_structure": has_graph}


# ── Change Management: zamykání uzlů + historie verzí ─────────────
def _graph_path(pid: str) -> Path:
    return project_paths(pid) / "output" / "structure_graph.json"


def _load_graph_data(pid: str) -> Optional[dict]:
    p = _graph_path(pid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_graph_data(pid: str, data: dict) -> None:
    _graph_path(pid).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _history_archive(base_out: Path, node_key: str, content: str, section_ext: str = ".md") -> str:
    """Uloží verzi sekce do output/history/{key}_{timestamp}{ext} (kompatibilní s book_builder._archive_section)."""
    history_dir = base_out / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    ms = int(time.time() * 1000) % 1000
    ts = time.strftime("%Y%m%dT%H%M%S") + f"-{ms:03d}"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(node_key))
    target = history_dir / f"{safe}_{ts}{section_ext}"
    target.write_text(content, encoding="utf-8")
    return target.name


@app.put("/api/projects/{pid}/structure/lock")
def set_node_lock(pid: str, payload: dict):
    _read_meta(pid)
    node_key = str(payload.get("node_key") or "").strip()
    locked = bool(payload.get("locked"))
    data = _load_graph_data(pid)
    if not data or "nodes" not in data:
        raise HTTPException(404, "Struktura zatím neexistuje")
    if node_key not in data["nodes"]:
        raise HTTPException(404, f"Uzel {node_key} neexistuje")
    data["nodes"][node_key]["locked"] = locked
    _save_graph_data(pid, data)
    return {"ok": True, "node_key": node_key, "locked": locked}


@app.get("/api/projects/{pid}/output/history")
def get_history(pid: str, section: str):
    _read_meta(pid)
    base = (project_paths(pid) / "output").resolve()
    hist = base / "history"
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(section))
    files = []
    if hist.exists():
        for f in hist.iterdir():
            if f.is_file() and f.name.startswith(safe + "_") and f.suffix in (".md", ".tex"):
                files.append({"name": f.name, "size": f.stat().st_size, "mtime": float(f.stat().st_mtime)})
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return {"section": section, "files": files}


@app.post("/api/projects/{pid}/output/history/restore")
def restore_history(pid: str, payload: dict):
    _read_meta(pid)
    section = str(payload.get("section") or "").strip()
    fname = str(payload.get("file") or "").strip()
    if "/" in fname or "\\" in fname or ".." in fname or not section:
        raise HTTPException(400, "Neplatné parametry")
    base = (project_paths(pid) / "output").resolve()
    hist = (base / "history").resolve()
    src = (hist / fname).resolve()
    if not str(src).startswith(str(base)) or not src.is_file():
        raise HTTPException(404, "Verze neexistuje")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", section)
    target = base / "sections" / f"{safe}.md"
    # archivuj aktuální verzi, než ji přepíšeme
    if target.exists():
        try:
            _cur = target.read_text(encoding="utf-8", errors="replace")
        except Exception:
            _cur = ""
        if _cur.strip():
            _history_archive(base, section, _cur)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    # obnovený obsah je ručně upravený → ochraň ho před hromadným přepisem
    data = _load_graph_data(pid)
    if data and "nodes" in data and safe in data["nodes"]:
        data["nodes"][safe]["manual_override"] = True
        data["nodes"][safe]["locked"] = True
        _save_graph_data(pid, data)
    return {"ok": True, "restored": src.name}


@app.post("/api/projects/{pid}/output/history/snapshot")
def snapshot_history(pid: str, payload: dict):
    _read_meta(pid)
    section = str(payload.get("section") or "").strip()
    if not section:
        raise HTTPException(400, "Chybí section")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", section)
    base = (project_paths(pid) / "output").resolve()
    target = base / "sections" / f"{safe}.md"
    if not target.is_file():
        raise HTTPException(404, "Sekce zatím není vygenerovaná")
    name = _history_archive(base, section, target.read_text(encoding="utf-8", errors="replace"))
    return {"ok": True, "name": name}


@app.post("/api/projects/{pid}/translate-node")
def translate_node(pid: str, payload: dict):
    """Rychlý překlad stávajícího textu uzlu (bez spouštění celé RAG pipeline)."""
    _read_meta(pid)
    node_id = str(payload.get("node_id") or "").strip().replace(".", "-")
    path = str(payload.get("path") or "").strip()
    target_lang = str(payload.get("target_lang") or "").strip() or "Čeština"
    model = str(payload.get("model") or "").strip()
    base = (project_paths(pid) / "output").resolve()
    if node_id:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", node_id)
        target = (base / "sections" / f"{safe}.md").resolve()
        path = f"sections/{safe}.md"
    elif path:
        target = (base / path).resolve()
    else:
        raise HTTPException(400, "Chybí node_id nebo path")
    if not str(target).startswith(str(base)) or not target.is_file():
        raise HTTPException(404, "Soubor neexistuje")
    text = target.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        raise HTTPException(400, "Soubor je prázdný")
    llm = OpenRouterLLM()
    sys = (
        "Jsi profesionální akademický překladatel. Přelož následující text do jazyka "
        f"{target_lang}. Zachovej veškerou strukturaci v Markdownu, LaTeXové citace, vzorce a "
        "specifikace. Zachovej klíčové anglické odborné termíny v závorce tam, kde je to vhodné. "
        "Vrať POUZE přeložený text, bez úvodních komentářů nebo shrnutí."
    )
    try:
        translated = (llm.chat(
            [{"role": "system", "content": sys}, {"role": "user", "content": text}],
            model=model or None,
        ) or "").strip()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Překlad selhal: {e}")
    if not translated:
        raise HTTPException(502, "Překlad vrátil prázdný text")
    section_key = node_id or (Path(path).stem if path else "")
    if section_key:
        _history_archive(base, section_key, text)
    target.write_text(translated, encoding="utf-8")
    # přeložený obsah = ručně upravený → chraň proti hromadnému přepisu
    data = _load_graph_data(pid)
    if data and section_key and section_key in data.get("nodes", {}):
        data["nodes"][section_key]["manual_override"] = True
        data["nodes"][section_key]["locked"] = True
        _save_graph_data(pid, data)
    return {"ok": True, "content": translated, "path": path}


@app.put("/api/projects/{pid}/output/section")
def save_section(pid: str, payload: dict):
    """Uloží ručně upravený obsah sekce (editovatelný náhled)."""
    _read_meta(pid)
    node_id = str(payload.get("node_id") or "").strip().replace(".", "-")
    content = str(payload.get("content") or "")
    if not node_id:
        raise HTTPException(400, "Chybí node_id")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", node_id)
    base = (project_paths(pid) / "output").resolve()
    target = (base / "sections" / f"{safe}.md").resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(400, "Neplatná cesta")
    # před přepisem archivuj aktuální verzi
    if target.is_file():
        try:
            prev = target.read_text(encoding="utf-8", errors="replace")
        except Exception:
            prev = ""
        if prev.strip() and prev != content:
            _history_archive(base, node_id, prev)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    # ruční editace → označ jako ručně upravenou (chrání proti hromadnému přepisu)
    data = _load_graph_data(pid)
    if data and node_id in data.get("nodes", {}):
        data["nodes"][node_id]["manual_override"] = True
        _save_graph_data(pid, data)
    return {"ok": True, "path": str(target.relative_to(base))}


# ── Prompt Management (editor promptů) ────────────────────────────
from autogenbook.prompts.book_loader import load_book_prompts  # noqa: E402

EDITABLE_PROMPT_KEYS = [
    "book_section_writer_system",
    "book_section_writer_user",
    "book_section_reviewer_system",
    "book_section_reviewer_user",
    "book_section_revision_system",
    "book_section_revision_user",
    "book_json_from_txt_system",
    "book_json_from_txt_user",
    "structure_subdivider_system",
    "structure_subdivider_user",
    "length_control_user",
    "context_memory_user",
    "global_system_policy",
]

GLOBAL_PROMPTS_FILE = REPO_ROOT / "global_prompts.json"


def _default_prompts() -> dict:
    try:
        all_prompts = load_book_prompts(content_format="markdown")
    except Exception:
        all_prompts = {}
    return {k: all_prompts.get(k, "") for k in EDITABLE_PROMPT_KEYS}


def _load_global_overrides() -> dict:
    if GLOBAL_PROMPTS_FILE.exists():
        try:
            data = json.loads(GLOBAL_PROMPTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _save_global_overrides(data: dict) -> None:
    try:
        GLOBAL_PROMPTS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except PermissionError as e:
        raise HTTPException(500, f"Nemohu uložit globální prompty: {e}") from e


@app.get("/api/projects/{pid}/prompts")
def get_project_prompts(pid: str):
    meta = _read_meta(pid)
    defaults = _default_prompts()
    global_ovr = _load_global_overrides()
    project_ovr = (meta.get("prompts") or {}) if isinstance(meta.get("prompts"), dict) else {}
    keys = EDITABLE_PROMPT_KEYS
    effective = {
        k: project_ovr.get(k) or global_ovr.get(k) or defaults.get(k, "")
        for k in keys
    }
    return {
        "keys": keys,
        "defaults": defaults,
        "global": global_ovr,
        "project": project_ovr,
        "effective": effective,
    }


@app.put("/api/projects/{pid}/prompts")
def save_project_prompts(pid: str, payload: dict):
    meta = _read_meta(pid)
    overrides = payload.get("overrides")
    if not isinstance(overrides, dict):
        raise HTTPException(400, "overrides musí být objekt")
    cur = dict(meta.get("prompts") or {})
    for k, v in overrides.items():
        if k not in EDITABLE_PROMPT_KEYS:
            continue
        if isinstance(v, str) and v.strip():
            cur[k] = v
        else:
            cur.pop(k, None)  # null/prázdné → reset na výchozí
    meta["prompts"] = cur
    meta["updated"] = _now()
    _write_meta(pid, meta)
    return {"ok": True, "project": cur}


@app.get("/api/prompts/global")
def get_global_prompts():
    defaults = _default_prompts()
    return {"keys": EDITABLE_PROMPT_KEYS, "defaults": defaults, "global": _load_global_overrides()}


@app.put("/api/prompts/global")
def save_global_prompts(payload: dict):
    overrides = payload.get("overrides")
    if not isinstance(overrides, dict):
        raise HTTPException(400, "overrides musí být objekt")
    clean = {}
    for k, v in overrides.items():
        if k not in EDITABLE_PROMPT_KEYS:
            continue
        if isinstance(v, str) and v.strip():
            clean[k] = v
    _save_global_overrides(clean)
    return {"ok": True, "global": clean}


# ── Globální konfigurace (Tavily API klíč pro Web RAG) ──────────
def _tavily_status() -> dict:
    key = resolve_tavily_key()
    if os.environ.get("TAVILY_API_KEY", "").strip():
        source = "env"
    elif load_env_file(REPO_ROOT / ".env").get("TAVILY_API_KEY", "").strip():
        source = "dotenv"
    elif key:
        source = "config"
    else:
        source = None
    masked = (key[:6] + "…" + key[-4:]) if key and len(key) > 12 else ("••••••••" if key else "")
    return {"configured": bool(key), "source": source, "masked": masked}


@app.get("/api/config/tavily")
def get_config_tavily():
    return _tavily_status()


@app.put("/api/config/tavily")
def put_config_tavily(payload: dict):
    key = str(payload.get("api_key") or "").strip()
    try:
        save_tavily_key(key)
    except PermissionError as e:
        raise HTTPException(500, f"Nemohu uložit Tavily klíč: {e}") from e
    return {"ok": True, "tavily": _tavily_status()}
