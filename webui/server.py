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

from .runner import RunError, runner

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = REPO_ROOT / "projects"
PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)

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
    (project_paths(pid) / "project.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


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


# ── Run ────────────────────────────────────────────────────────────
def _build_argv(pid: str, cfg: dict) -> list[str]:
    p = project_paths(pid)
    spec = p / "spec.txt"
    out = p / "output"
    kb = p / "kb"
    argv = [
        "python",
        str(REPO_ROOT / "main.py"),
        "--mode", cfg.get("mode", "book"),
        "--input", str(spec),
        "--out-dir", str(out),
    ]
    kb_files = [f for f in kb.iterdir() if f.is_file() and not f.name.startswith(".")] if kb.exists() else []
    if kb_files:
        argv += ["--kb-dir", str(kb)]
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
