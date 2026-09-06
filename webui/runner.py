"""Subprocess runner: starts / stops book runs, streams the log, tracks state."""
from __future__ import annotations

import os
import json
import signal
import subprocess
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_CONFIG_FILE = REPO_ROOT / "global_config.json"


class RunError(Exception):
    pass


def load_env_file(path: Path) -> dict:
    """Parse a simple KEY=VALUE .env file (comments + quotes stripped)."""
    env = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _load_global_config() -> dict:
    """Načte globální konfiguraci serveru (např. uložený Tavily klíč)."""
    if GLOBAL_CONFIG_FILE.exists():
        try:
            data = json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def resolve_tavily_key() -> str:
    """Vrátí Tavily API klíč s prioritou: systémové prostředí → .env → globální konfigurace."""
    val = os.environ.get("TAVILY_API_KEY", "").strip()
    if val:
        return val
    val = load_env_file(REPO_ROOT / ".env").get("TAVILY_API_KEY", "").strip()
    if val:
        return val
    val = str(_load_global_config().get("tavily_api_key", "") or "").strip()
    return val


def save_tavily_key(key: str) -> str:
    """Uloží Tavily klíč do globální konfigurace serveru (prázdný klíč = smazat)."""
    data = _load_global_config()
    key = key.strip()
    if key:
        data["tavily_api_key"] = key
    else:
        data.pop("tavily_api_key", None)
    GLOBAL_CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return key


class Runner:
    def __init__(self) -> None:
        self._procs: dict[str, subprocess.Popen] = {}
        self._state: dict[str, dict] = {}

    def start(self, project: dict, argv: list[str], extra_env: dict | None = None) -> dict:
        pid = project["id"]
        if self._state.get(pid, {}).get("status") == "running":
            raise RunError("Běh už probíhá")

        log_path = project["path"] / "run.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        env = dict(os.environ)
        env.update(load_env_file(REPO_ROOT / ".env"))
        if extra_env:
            env.update(extra_env)
        env.setdefault("AUTOGENBOOK_NONINTERACTIVE", "1")
        env.setdefault("AUTOGENBOOK_ASSUME_YES", "1")
        env.setdefault("PYTHONUTF8", "1")
        # Tavily API klíč pro Web RAG – předat ho CLI podprocesu (ať už je odkudkoli).
        if not env.get("TAVILY_API_KEY"):
            tk = resolve_tavily_key()
            if tk:
                env["TAVILY_API_KEY"] = tk

        logf = log_path.open("a", encoding="utf-8")
        popen_kwargs = dict(
            cwd=str(REPO_ROOT),
            env=env,
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if os.name == "posix":
            # vlastní session + procesní skupina → pause/(re)start/kill ovlivní celý strom
            popen_kwargs["start_new_session"] = True
        proc = subprocess.Popen(argv, **popen_kwargs)
        state = {
            "status": "running",
            "pid": proc.pid,
            "log_path": str(log_path),
            "started": time.time(),
            "finished": None,
            "exit_code": None,
            "argv": argv,
        }
        self._procs[pid] = proc
        self._state[pid] = state
        threading.Thread(target=self._watch, args=(pid, proc, state), daemon=True).start()
        return state

    def _watch(self, pid, proc, state):
        code = proc.wait()
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        state["exit_code"] = code
        state["finished"] = time.time()
        cancelled = state.get("cancelled", False)
        state["status"] = "cancelled" if cancelled else ("done" if code == 0 else "error")
        self._procs.pop(pid, None)
        try:
            with open(state["log_path"], "a", encoding="utf-8") as f:
                f.write(f"\n[ui] Běh skončil: status={state['status']} exit={code}\n")
        except Exception:
            pass

    def _pgid(self, pid: str):
        proc = self._procs.get(pid)
        if proc is None or os.name != "posix":
            return None
        try:
            return os.getpgid(proc.pid)
        except (ProcessLookupError, PermissionError):
            return None

    def pause(self, pid: str) -> bool:
        pgid = self._pgid(pid)
        if pgid is None:
            return False
        try:
            os.killpg(pgid, signal.SIGSTOP)
            self._state[pid]["paused"] = True
            return True
        except Exception:
            return False

    def resume(self, pid: str) -> bool:
        pgid = self._pgid(pid)
        if pgid is None:
            return False
        try:
            os.killpg(pgid, signal.SIGCONT)
            self._state[pid]["paused"] = False
            return True
        except Exception:
            return False

    def cancel(self, pid: str) -> bool:
        if pid not in self._procs:
            return False
        self._state[pid]["cancelled"] = True
        pgid = self._pgid(pid)
        try:
            if pgid is not None:
                os.killpg(pgid, signal.SIGCONT)  # aby signály prošly i při pozastavení
                os.killpg(pgid, signal.SIGTERM)
            else:
                self._procs[pid].terminate()
        except Exception:
            try:
                self._procs[pid].kill()
            except Exception:
                pass
        # eskalace na SIGKILL, pokud proces do 3 s neskončí
        def _escalate():
            time.sleep(3)
            if self.status(pid).get("status") == "running":
                try:
                    if pgid is not None:
                        os.killpg(pgid, signal.SIGKILL)
                    else:
                        self._procs[pid].kill()
                except Exception:
                    pass
        threading.Thread(target=_escalate, daemon=True).start()
        return True

    def status(self, pid: str) -> dict:
        return self._state.get(pid, {"status": "idle"})

    def tail(self, pid: str, log_path: Path):
        """SSE generator: tail run.log from the current end, then emit final status."""
        import json

        pos = log_path.stat().st_size if log_path.exists() else 0
        while True:
            state = self.status(pid)
            if log_path.exists():
                size = log_path.stat().st_size
                if size > pos:
                    with open(log_path, encoding="utf-8", errors="replace") as f:
                        f.seek(pos)
                        data = f.read()
                    pos = size
                    for line in data.splitlines():
                        yield f"data: {json.dumps({'type': 'log', 'text': line})}\n\n"
            status = state.get("status")
            if status != "running":
                yield f"data: {json.dumps({'type': 'status', 'status': status, 'exit': state.get('exit_code')})}\n\n"
                break
            time.sleep(0.25)
        yield "data: " + json.dumps({"type": "close"}) + "\n\n"


runner = Runner()
