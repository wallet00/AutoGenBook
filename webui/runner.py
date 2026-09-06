"""Subprocess runner: starts / stops book runs, streams the log, tracks state."""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


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

        logf = log_path.open("a", encoding="utf-8")
        proc = subprocess.Popen(
            argv,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=logf,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
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

    def cancel(self, pid: str) -> bool:
        if pid in self._procs:
            self._state[pid]["cancelled"] = True
            try:
                self._procs[pid].terminate()
            except Exception:
                pass
            return True
        return False

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
