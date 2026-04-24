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
    openai_api_key: str | None
    openai_base_url: str
    openai_timeout_seconds: float
    deepseek_api_key: str | None
    deepseek_base_url: str
    qwen_api_key: str | None
    qwen_base_url: str
    kimi_api_key: str | None
    kimi_base_url: str


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
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30")),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("AI_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        qwen_api_key=os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("AI_API_KEY"),
        qwen_base_url=os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
        kimi_api_key=os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or os.getenv("AI_API_KEY"),
        kimi_base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1"),
    )
