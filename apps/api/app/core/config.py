from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str
    seed_data_dir: Path
    api_host: str
    api_port: int
    embedding_provider: str
    embedding_model: str
    recommendation_provider: str
    recommendation_model: str


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot",
        ),
        seed_data_dir=Path(os.getenv("SEED_DATA_DIR", "data/seed")),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "local_hash"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "local-hash-embedding-v1"),
        recommendation_provider=os.getenv("RECOMMENDATION_PROVIDER", "deterministic"),
        recommendation_model=os.getenv("RECOMMENDATION_MODEL", "deterministic_ranker_with_citations"),
    )
