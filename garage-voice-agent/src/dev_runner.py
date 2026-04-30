from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import certifi

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
LOG_ROOT = PROJECT_ROOT / "logs"


@dataclass(frozen=True)
class Service:
    name: str
    command: list[str]
    cwd: Path
    log_path: Path


def _services() -> list[Service]:
    return [
        Service(
            "agent",
            [sys.executable, "src/agent.py", "dev"],
            PROJECT_ROOT,
            LOG_ROOT / "backend" / "agent.log",
        ),
        Service(
            "api",
            [sys.executable, "-m", "uvicorn", "api.main:app", "--reload", "--port", "8000"],
            PROJECT_ROOT,
            LOG_ROOT / "backend" / "api.log",
        ),
        Service(
            "web",
            ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"],
            FRONTEND_DIR,
            LOG_ROOT / "frontend" / "web.log",
        ),
    ]


def _stream_output(name: str, process: subprocess.Popen[str], log_path: Path) -> None:
    assert process.stdout is not None
    with log_path.open("a", encoding="utf-8") as log_file:
        for line in process.stdout:
            log_file.write(line)
            log_file.flush()
            print(f"[{name}] {line}", end="", flush=True)


def _start_service(service: Service) -> subprocess.Popen[str]:
    if service.name == "web" and not (FRONTEND_DIR / "node_modules").exists():
        raise RuntimeError("frontend/node_modules introuvable. Lance d'abord: cd frontend && npm install")

    service.log_path.parent.mkdir(parents=True, exist_ok=True)
    service.log_path.write_text("", encoding="utf-8")

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("SSL_CERT_FILE", certifi.where())
    env.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
    env.setdefault("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    process = subprocess.Popen(
        service.command,
        cwd=service.cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    thread = threading.Thread(target=_stream_output, args=(service.name, process, service.log_path), daemon=True)
    thread.start()
    return process


def _stop_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()

    deadline = time.time() + 8
    for process in processes:
        remaining = max(0.1, deadline - time.time())
        try:
            process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            process.kill()


def main() -> int:
    print("Starting Auto Voice Agent dev stack")
    print("API: http://127.0.0.1:8000")
    print("Frontend: http://127.0.0.1:3000/demo")
    print(f"Backend logs: {LOG_ROOT / 'backend'}")
    print(f"Frontend logs: {LOG_ROOT / 'frontend'}")
    print("Press Ctrl+C to stop all services.\n")

    processes: list[subprocess.Popen[str]] = []

    def handle_signal(signum: int, _frame: object) -> None:
        print(f"\nReceived signal {signum}. Stopping services...")
        _stop_processes(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        for service in _services():
            processes.append(_start_service(service))

        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    print(f"\nA service exited with code {code}. Stopping the dev stack.")
                    _stop_processes(processes)
                    return code
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping services...")
        _stop_processes(processes)
        return 0
    except Exception as exc:
        print(f"\nDev stack failed: {exc}", file=sys.stderr)
        _stop_processes(processes)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
