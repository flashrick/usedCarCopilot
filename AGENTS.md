# AGENTS.md

## Repository Status

This repository is currently in the data-preparation stage for AI Used Car Decision Copilot. Product planning documents live in `documents/`, and the first seed dataset lives in `data/seed/`.

## Project Intent

Treat this project as a portfolio-grade AI engineering system, not a generic chatbot. Work should preserve the core emphasis on RAG, hybrid retrieval, structured listing filters, citations, evaluation, observability, and deployable API/UI packaging.

## Editing Boundaries

- Keep original source notes in `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md` unless the user explicitly asks to revise them.
- Prefer adding derived planning and implementation docs as separate files instead of rewriting the source notes.
- Do not add speculative commands to documentation unless they are backed by actual project files.
- Treat `data/seed/` as the canonical input for ingestion and retrieval work.
- Treat `data/raw/` as source exports that can be regenerated or normalized.

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

There are no application build, lint, test, or run commands yet. Do not claim app commands are available until package manifests, backend config, or scripts have been added.

## Next Expected Work

The next technical step is application scaffolding:

- `apps/web`
- `apps/api`
- `packages/prompts`
- `packages/retrieval`
- `packages/evaluation`
- `data/raw`
- `data/processed`
- `scripts`

After scaffolding, update this file with real app commands and concrete path ownership.
