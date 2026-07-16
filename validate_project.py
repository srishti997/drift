from __future__ import annotations

import compileall
import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    PROJECT_ROOT / "dashboard.py",
    PROJECT_ROOT / "run_drift.py",
    PROJECT_ROOT / "backend" / "main.py",
    PROJECT_ROOT / "backend" / "history_engine.py",
    PROJECT_ROOT / "ui" / "replay_page.py",
    PROJECT_ROOT / "ui" / "history_page.py",
    PROJECT_ROOT / "requirements.txt",
    PROJECT_ROOT / ".gitignore",
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / ".env.example",
    PROJECT_ROOT / "ui" / "chat_page.py",
    PROJECT_ROOT / "backend" / "chat_engine.py",
]

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "streamlit",
    "requests",
    "pandas",
    "plotly",
]

def check_secrets() -> list[str]:
    failures = []

    files_to_scan = [
        PROJECT_ROOT / "backend" / "llm_client.py",
        PROJECT_ROOT / "dashboard.py",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / ".env.example",
    ]

    suspicious_terms = [
        "API KEY:",
        "AIza",
        "AQ.",
    ]

    for file_path in files_to_scan:
        if not file_path.exists():
            continue

        content = file_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for term in suspicious_terms:
            if term in content:
                message = (
                    f"Possible secret found in "
                    f"{file_path.relative_to(PROJECT_ROOT)}: "
                    f"{term}"
                )
                print(f"[FAIL] {message}")
                failures.append(message)

    if not failures:
        print("[PASS] No obvious secrets found in source files")

    return failures

def check_required_files() -> list[str]:
    failures = []

    for file_path in REQUIRED_FILES:
        relative_path = file_path.relative_to(PROJECT_ROOT)

        if file_path.exists():
            print(f"[PASS] File exists: {relative_path}")
        else:
            message = f"Missing file: {relative_path}"
            print(f"[FAIL] {message}")
            failures.append(message)

    return failures


def check_python_syntax() -> list[str]:
    failures = []

    folders = [
        PROJECT_ROOT / "backend",
        PROJECT_ROOT / "ui",
    ]

    top_level_files = [
        PROJECT_ROOT / "dashboard.py",
        PROJECT_ROOT / "run_drift.py",
    ]

    for file_path in top_level_files:
        if not file_path.exists():
            continue

        try:
            source = file_path.read_text(encoding="utf-8")
            compile(source, str(file_path), "exec")
            print(
                f"[PASS] Syntax valid: "
                f"{file_path.relative_to(PROJECT_ROOT)}"
            )
        except SyntaxError as error:
            message = (
                f"Syntax error in "
                f"{file_path.relative_to(PROJECT_ROOT)}: "
                f"line {error.lineno}: {error.msg}"
            )
            print(f"[FAIL] {message}")
            failures.append(message)

    for folder in folders:
        if not folder.exists():
            continue

        success = compileall.compile_dir(
            folder,
            quiet=1,
            force=True,
        )

        if success:
            print(
                f"[PASS] Python files compile: "
                f"{folder.relative_to(PROJECT_ROOT)}"
            )
        else:
            message = (
                f"Compilation failed in "
                f"{folder.relative_to(PROJECT_ROOT)}"
            )
            print(f"[FAIL] {message}")
            failures.append(message)

    return failures


def check_packages() -> list[str]:
    failures = []

    for package in REQUIRED_PACKAGES:
        if importlib.util.find_spec(package) is not None:
            print(f"[PASS] Package installed: {package}")
        else:
            message = f"Package not installed: {package}"
            print(f"[FAIL] {message}")
            failures.append(message)

    return failures


def check_gitignore() -> list[str]:
    failures = []
    gitignore_path = PROJECT_ROOT / ".gitignore"

    if not gitignore_path.exists():
        return ["Missing .gitignore"]

    content = gitignore_path.read_text(encoding="utf-8")

    required_entries = [
        ".env",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "venv/",
    ]

    for entry in required_entries:
        if entry in content:
            print(f"[PASS] .gitignore contains: {entry}")
        else:
            message = f".gitignore missing: {entry}"
            print(f"[FAIL] {message}")
            failures.append(message)

    return failures


def check_json_files() -> list[str]:
    failures = []

    json_files = [
        PROJECT_ROOT / "data" / "activity_logs.json",
        PROJECT_ROOT / "data" / "users.json",
    ]

    for file_path in json_files:
        if not file_path.exists():
            print(
                f"[INFO] JSON file not created yet: "
                f"{file_path.relative_to(PROJECT_ROOT)}"
            )
            continue

        try:
            with file_path.open("r", encoding="utf-8") as file:
                json.load(file)

            print(
                f"[PASS] Valid JSON: "
                f"{file_path.relative_to(PROJECT_ROOT)}"
            )

        except json.JSONDecodeError as error:
            message = (
                f"Invalid JSON in "
                f"{file_path.relative_to(PROJECT_ROOT)}: "
                f"line {error.lineno}, column {error.colno}"
            )
            print(f"[FAIL] {message}")
            failures.append(message)

    return failures


def main() -> None:
    print("=" * 65)
    print("Drift Project Validation")
    print("=" * 65)

    failures = []

    failures.extend(check_required_files())
    failures.extend(check_python_syntax())
    failures.extend(check_packages())
    failures.extend(check_gitignore())
    failures.extend(check_json_files())
    failures.extend(check_secrets())

    print()
    print("=" * 65)

    if failures:
        print(f"Validation failed with {len(failures)} issue(s):")

        for failure in failures:
            print(f" - {failure}")

        sys.exit(1)

    print("Validation completed successfully.")
    print("Drift is ready to run.")
    print("=" * 65)
    

if __name__ == "__main__":
    main()
    