from __future__ import annotations

import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_URL = "http://127.0.0.1:8000"
DASHBOARD_URL = "http://localhost:8501"


def start_process(command: list[str], name: str) -> subprocess.Popen:
    print(f"[Drift] Starting {name}...")

    return subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
    )


def terminate_process(process: subprocess.Popen | None, name: str) -> None:
    if process is None or process.poll() is not None:
        return

    print(f"[Drift] Stopping {name}...")

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main() -> None:
    backend_process: subprocess.Popen | None = None
    dashboard_process: subprocess.Popen | None = None

    try:
        backend_process = start_process(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
                "--reload",
            ],
            "FastAPI backend",
        )

        time.sleep(2)

        if backend_process.poll() is not None:
            raise RuntimeError(
                "Backend stopped during startup. "
                "Check the terminal output for the error."
            )

        dashboard_process = start_process(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "dashboard.py",
                "--server.port",
                "8501",
            ],
            "Streamlit dashboard",
        )

        time.sleep(3)

        if dashboard_process.poll() is not None:
            raise RuntimeError(
                "Dashboard stopped during startup. "
                "Check the terminal output for the error."
            )

        print()
        print("=" * 60)
        print("Drift is running")
        print(f"Backend:  {BACKEND_URL}")
        print(f"API docs: {BACKEND_URL}/docs")
        print(f"Dashboard:{DASHBOARD_URL}")
        print("Press Ctrl+C to stop everything.")
        print("=" * 60)

        webbrowser.open(DASHBOARD_URL)

        while True:
            if backend_process.poll() is not None:
                raise RuntimeError(
                    "The backend process stopped unexpectedly."
                )

            if dashboard_process.poll() is not None:
                raise RuntimeError(
                    "The Streamlit process stopped unexpectedly."
                )

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Drift] Shutdown requested.")

    except Exception as error:
        print(f"\n[Drift] Error: {error}")

    finally:
        terminate_process(dashboard_process, "Streamlit dashboard")
        terminate_process(backend_process, "FastAPI backend")
        print("[Drift] Shutdown complete.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.default_int_handler)
    main()