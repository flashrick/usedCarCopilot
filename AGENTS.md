# AGENTS.md

## Repository Status

This repository is currently in the planning stage for AI Used Car Decision Copilot. The only established source materials are in `documents/`.

## Project Intent

Treat this project as a portfolio-grade AI engineering system, not a generic chatbot. Work should preserve the core emphasis on RAG, hybrid retrieval, structured listing filters, citations, evaluation, observability, and deployable API/UI packaging.

## Editing Boundaries

- Keep original source notes in `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md` unless the user explicitly asks to revise them.
- Prefer adding derived planning and implementation docs as separate files instead of rewriting the source notes.
- Do not introduce implementation code until the repo structure and initial contracts are clear.
- Do not add speculative commands to documentation unless they are backed by actual project files.

## Documentation Conventions

- Use `documents/` for project documentation while this repo remains documentation-first.
- Keep public-facing GitHub copy in the root `README.md`.
- Keep long-running execution state in `PLANS.md`.
- When adding architecture or implementation docs, connect them back to the MVP: search, recommendations, details, comparison, citations, risk scoring, and evaluation.

## Current Validation

There are no build, lint, test, or run commands yet. Do not claim any command is available until package manifests, backend config, or scripts have been added.

## Next Expected Work

The next technical step is repository scaffolding:

- `apps/web`
- `apps/api`
- `packages/prompts`
- `packages/retrieval`
- `packages/evaluation`
- `data/raw`
- `data/processed`
- `scripts`

After scaffolding, update this file with real commands and concrete path ownership.

