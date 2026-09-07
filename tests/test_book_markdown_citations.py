"""Ověření: (1) MD výstup bez surového \\cite + oddíl Literatura,
(2) helper _collect_child_texts, (3) mapování include_child_texts přes server."""
import json
import tempfile
from pathlib import Path

import networkx as nx
import pytest

import book_builder as BB


def _build_graph(tmp: Path) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("book", title="Test Book")
    g.add_node("1", title="Kapitola 1", content_file_path=str(tmp / "sections" / "1.md"))
    g.add_node("1-1", title="Podkapitola", content_file_path=str(tmp / "sections" / "1-1.md"))
    g.add_node("1-2", title="Podkapitola 2", content_file_path=str(tmp / "sections" / "1-2.md"))
    g.add_edge("book", "1")
    g.add_edge("1", "1-1")
    g.add_edge("1", "1-2")
    return g


def test_markdown_document_strips_cite_and_adds_references(tmp_path):
    (tmp_path / "sections").mkdir(parents=True)
    (tmp_path / "sections" / "1.md").write_text("Intro with \\cite{file} a \\cite{unknown_x}.\n", encoding="utf-8")
    (tmp_path / "sections" / "1-1.md").write_text("Sub \\cite{file}.\n", encoding="utf-8")
    (tmp_path / "sections" / "1-2.md").write_text("Another \\cite{other}.\n", encoding="utf-8")
    (tmp_path / "kb_sources.json").write_text(json.dumps({"chunks": [
        {"source_path": "KB/zdroj.pdf", "loc": "Strana 5", "rid": "r1", "cite_key": "file", "excerpt": "Obsah zdroje"},
        {"source_path": "KB/druhy.pdf", "loc": "Strana 2", "rid": "r2", "cite_key": "other", "excerpt": "Obsah druhy"},
    ]}), encoding="utf-8")

    g = _build_graph(tmp_path)
    md = BB.build_markdown_document(g, out_dir=tmp_path)
    txt = md.read_text(encoding="utf-8")
    assert "\\cite" not in txt
    assert "## Literatura" in txt
    assert "[1]" in txt and "[2]" in txt
    # ‚unknown_x‘ není v KB → volný marker se odstraní (žádný odkaz)
    assert "unknown_x" not in txt


def test_collect_child_texts_in_order(tmp_path):
    (tmp_path / "sections").mkdir(parents=True)
    g = _build_graph(tmp_path)
    for k, body in (("1-1", "AAA"), ("1-2", "BBB")):
        (tmp_path / "sections" / f"{k}.md").write_text(body, encoding="utf-8")
    ctx = BB._collect_child_texts(g, "1", tmp_path / "sections", ".md")
    assert "### Podkapitola" in ctx
    assert "### Podkapitola 2" in ctx
    assert ctx.index("AAA") < ctx.index("BBB")


def test_node_env_maps_include_child_texts():
    from webui import server as S
    env = S._node_env("pid", {"mode": "single_node", "include_child_texts": True, "gen_mode": "full"})
    params = json.loads(env["AUTOGENBOOK_NODE_PARAMS"])
    assert params.get("include_child_texts") is True
    # default (bez vlajky) → nemá být nastaveno
    env2 = S._node_env("pid", {"mode": "single_node", "gen_mode": "full"})
    assert "include_child_texts" not in json.loads(env2["AUTOGENBOOK_NODE_PARAMS"])


def test_node_env_applies_to_branch_mode():
    from webui import server as S
    env = S._node_env("pid", {
        "mode": "branch", "gen_mode": "enrich",
        "custom_prompt": "Piš pěkně", "include_child_texts": True,
        "kb_files": ["a.pdf"]})
    params = json.loads(env["AUTOGENBOOK_NODE_PARAMS"])
    assert params["gen_mode"] == "enrich"
    assert params["include_existing"] is True
    assert params["custom_prompt"] == "Piš pěkně"
    assert params["include_child_texts"] is True
    assert params["kb_files"] == ["a.pdf"]
    # režim book (hromadný) parametry nenastavuje
    import os
    os.environ.pop("AUTOGENBOOK_NODE_PARAMS", None)
    env_book = S._node_env("pid", {"mode": "book", "gen_mode": "enrich"})
    assert env_book == {}


def test_build_argv_book_output_format(tmp_path, monkeypatch):
    import os
    os.environ.setdefault("AUTOGENBOOK_UI_PASSWORD", "x")
    from webui import server as S
    monkeypatch.setattr(S, "PROJECTS_ROOT", tmp_path)
    pid = "p"
    (tmp_path / pid / "output").mkdir(parents=True)
    (tmp_path / pid / "spec.txt").write_text("spec", encoding="utf-8")
    (tmp_path / pid / "project.json").write_text("{}", encoding="utf-8")

    # Markdown (výchozí): žádný --export-tex, PDF vypnuto
    argv_md = S._build_argv(pid, {"mode": "book", "pdf": False, "export_tex": False})
    assert "--export-tex" not in argv_md
    assert "--no-pdf" in argv_md

    # LaTeX: --export-tex
    argv_tex = S._build_argv(pid, {"mode": "book", "pdf": True, "export_tex": True})
    assert "--export-tex" in argv_tex
    assert "--no-pdf" not in argv_tex
