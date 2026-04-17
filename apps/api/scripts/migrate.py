#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.connection import get_connection


def main() -> None:
    migration_path = Path(__file__).resolve().parents[1] / "migrations" / "001_init.sql"
    sql = migration_path.read_text(encoding="utf-8")
    with get_connection() as connection:
        connection.execute(sql)
    print(f"Applied migration: {migration_path}")


if __name__ == "__main__":
    main()

