#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def run_step(relative_script_path: str) -> None:
    subprocess.run([sys.executable, relative_script_path], cwd=REPO_ROOT, check=True)


def main() -> None:
    run_step("apps/api/scripts/wait_for_db.py")
    run_step("apps/api/scripts/migrate.py")
    run_step("apps/api/scripts/ingest_seed.py")
    run_step("apps/api/scripts/build_embeddings.py")

    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "app.main:app",
            "--app-dir",
            "apps/api",
            "--host",
            os.getenv("API_HOST", "0.0.0.0"),
            "--port",
            os.getenv("API_PORT", "8000"),
        ],
    )


if __name__ == "__main__":
    main()
