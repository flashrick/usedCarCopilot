#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.ingestion.seed_loader import ingest_seed_data


def main() -> None:
    result = ingest_seed_data(get_settings().seed_data_dir)
    print("Seed ingestion completed")
    for key, value in result.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()

