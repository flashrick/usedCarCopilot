#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings


def main() -> None:
    timeout_seconds = int(os.getenv("DB_WAIT_TIMEOUT_SECONDS", "60"))
    interval_seconds = float(os.getenv("DB_WAIT_INTERVAL_SECONDS", "2"))
    deadline = time.monotonic() + timeout_seconds
    database_url = get_settings().database_url
    engine = create_engine(database_url, pool_pre_ping=True)

    while True:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1")).one()
            engine.dispose()
            print("Database is ready")
            return
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                engine.dispose()
                raise RuntimeError(
                    f"Database did not become ready within {timeout_seconds} seconds"
                ) from exc
            print("Waiting for database...", flush=True)
            time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
