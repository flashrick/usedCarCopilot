#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.connection import engine


def main() -> None:
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    migration_paths = sorted(migration_dir.glob("*.sql"))
    with engine.begin() as connection:
        for migration_path in migration_paths:
            sql = migration_path.read_text(encoding="utf-8")
            connection.exec_driver_sql(sql)
            print(f"Applied migration: {migration_path}")


if __name__ == "__main__":
    main()
