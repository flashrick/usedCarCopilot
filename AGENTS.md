# AGENTS.md

## Repository Status

This repository is currently in the early backend scaffolding stage for AI Used Car Decision Copilot. Product planning documents live in `documents/`, canonical seed data lives in `data/seed/`, and the first FastAPI/PostgreSQL backend lives in `apps/api/`.

## Project Intent

Treat this project as a portfolio-grade AI engineering system, not a generic chatbot. Work should preserve the core emphasis on RAG, hybrid retrieval, structured listing filters, citations, evaluation, observability, and deployable API/UI packaging.

## Editing Boundaries

- Keep original source notes in `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md` unless the user explicitly asks to revise them.
- Prefer adding derived planning and implementation docs as separate files instead of rewriting the source notes.
- Do not add speculative commands to documentation unless they are backed by actual project files.
- Treat `data/seed/` as the canonical input for ingestion and retrieval work.
- Treat `data/raw/` as source exports that can be regenerated or normalized.
- Keep database schema changes in `apps/api/migrations/`.
- Keep backend seed ingestion code in `apps/api/app/ingestion/` and command wrappers in `apps/api/scripts/`.
- Runtime database access must use SQLAlchemy ORM sessions and mapped records from `apps/api/app/db/orm.py`. Keep raw SQL limited to migrations or short health-check style probes.

## Documentation Conventions

- Use `documents/` for project documentation.
- Use `data/README.md` to explain dataset layout and coverage.
- Keep public-facing GitHub copy in the root `README.md`.
- Keep long-running execution state in `PLANS.md`.
- When adding architecture or implementation docs, connect them back to the MVP: search, recommendations, details, comparison, citations, risk scoring, and evaluation.

## Current Validation

Available data commands:

- Run `python3 scripts/prepare_seed_data.py` to normalize `data/raw/turners_listings.jsonl` into `data/seed/listings.jsonl`.
- Run `python3 scripts/validate_seed_data.py` to validate seed listings, knowledge sources, and eval cases.

Available backend commands:

- Run `docker compose up -d postgres` from the repo root to start PostgreSQL with pgvector.
- Run `pip install -e apps/api` after activating a Python virtual environment to install API dependencies.
- Run `python3 apps/api/scripts/migrate.py` from the repo root to apply the PostgreSQL schema.
- Run `python3 apps/api/scripts/ingest_seed.py` from the repo root to load seed data.
- Run `uvicorn app.main:app --app-dir apps/api --reload` from the repo root to start the API.

There are no frontend build, lint, test, or run commands yet.

## Next Expected Work

The next technical step is to run and verify the Postgres-backed backend locally, then add embedding generation and vector retrieval.
