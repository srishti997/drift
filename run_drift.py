import subprocess
import time
import webbrowser
import sys


def start_process(command, name):
    print(f"Starting {name}...")
    return subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def main():
    python_cmd = sys.executable

    backend = start_process(
        f"{python_cmd} -m uvicorn backend.main:app --reload",
        "Backend"
    )

    time.sleep(3)

    dashboard = start_process(
        f"{python_cmd} -m streamlit run dashboard.py",
        "Dashboard"
    )

    time.sleep(3)

    widget = start_process(
        f"{python_cmd} desktop_widget.py",
        "Desktop Widget"
    )

    webbrowser.open("http://localhost:8501")

    print("\nDrift is running.")
    print("Backend: http://127.0.0.1:8000")
    print("Dashboard: http://localhost:8501")
    print("\nPress CTRL+C to stop everything.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Drift...")
        backend.terminate()
        dashboard.terminate()
        widget.terminate()
        print("Stopped.")


if __name__ == "__main__":
    main()