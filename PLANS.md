# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through RAG, hybrid retrieval, structured filtering, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: data preparation and validation.

The repository now has planning documents plus a first seed dataset. Raw Turners listing data has been normalized into seed listings, model knowledge has been converted into JSONL, and eval cases are available for future retrieval and generation checks.

## Milestones

- Completed: choose portfolio project direction.
- Completed: create startup documentation package.
- Completed: create first raw Turners listing export.
- Completed: create canonical `data/seed/` layout for listings, knowledge sources, and eval cases.
- Completed: add data preparation and validation scripts.
- Completed: validate current seed data with no coverage warnings.
- Pending: scaffold repository structure for frontend, backend, data, scripts, and shared packages.
- Pending: define initial database schema from the seed data contract.
- Completed: add manual Honda Civic seed listing rows to close the listing coverage gap.
- Pending: build ingestion and embedding pipeline.
- Pending: build retrieval API and debug output.
- Pending: build recommendation API with citation-aware JSON output.
- Pending: build decision-workbench UI.
- Pending: add evaluation workflow and reporting.
- Pending: add deployment, screenshots, demo video, and public README polish.

## Accepted Decisions

- The project is a decision support system, not a generic chatbot.
- The MVP should be narrow before it is broad.
- Initial data scope should focus on Toyota, Mazda, and Honda.
- The first market is Auckland, New Zealand.
- The first listing source is Turners data normalized into `data/seed/listings.jsonl`.
- Canonical seed data lives in `data/seed/`; raw listing export lives in `data/raw/`.
- The technical direction is FastAPI, Next.js, PostgreSQL, and pgvector.
- The system must combine structured listing filters with unstructured semantic retrieval.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- No code scaffold exists yet.
- No API contract exists yet.
- No environment variable contract exists yet.

## Next Skill

Recommended next skill: `repo-architect`, followed by `backend-implementer`, `frontend-implementer`, and `test-engineer` once the scaffold and API contracts are clear.

## Next Actions

1. Create repository structure for `apps/web`, `apps/api`, `packages`, and application config.
2. Define the first database schema for listings, knowledge documents, chunks, embeddings, and eval cases.
3. Create `.env.example` with LLM, database, and app settings.
4. Implement ingestion before recommendation generation.

## Acceptance Gates

- Before implementation: product scope, schema, and API contracts are documented.
- Before frontend work: recommendation response JSON shape is stable enough for UI wiring.
- Before public release: README, architecture diagram, screenshots, demo script, eval report, and deployment links exist.
- Before LinkedIn posting: the app can run end to end and show citations, risk flags, and comparison output.

## Change Log

- Initial plan created from `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md`.
- Added canonical seed data layout, data preparation script, validation script, and updated project state after data validation.
- Added manual Honda Civic seed listing rows and cleared the listing coverage warning.
