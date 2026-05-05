# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through vehicle-profile RAG, hybrid retrieval, deterministic valuation, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: Vehicle-profile pivot with deterministic valuation implemented.

The repository now has planning documents, seed data, and a PostgreSQL-backed FastAPI scaffold centered on `vehicle_profiles` instead of live listings. The schema includes pgvector support and tables for vehicle profiles, knowledge sources, document chunks, chunk embeddings, eval cases, ingestion runs, and request logs. Runtime database access uses SQLAlchemy ORM sessions and mapped records. Seed ingestion now computes deterministic NZ valuation ranges per profile, local deterministic chunk embedding generation remains in place, pgvector semantic retrieval is profile-aware, and the recommendation flow compares user-selected vehicle profiles with citations and valuation summaries.

## Milestones

- Completed: choose portfolio project direction.
- Completed: create startup documentation package.
- Completed: create first raw Turners listing export.
- Completed: create canonical `data/seed/` layout for listings, knowledge sources, and eval cases.
- Completed: add data preparation and validation scripts.
- Completed: validate current seed data with no coverage warnings.
- Completed: scaffold repository structure for frontend placeholder, backend, shared packages, data, and scripts.
- Completed: define initial PostgreSQL and pgvector schema from the seed data contract.
- Completed: add manual Honda Civic seed listing rows to close the listing coverage gap.
- Completed: add local deterministic embedding generation for `document_chunks` and store vectors in `chunk_embeddings`.
- Completed: add first HTTP retrieval eval runner and baseline `documents/eval-report.md`.
- Completed: add deterministic citation-aware `POST /recommend` response contract.
- Completed: add first HTTP recommendation eval runner and baseline `documents/recommendation-eval-report.md`.
- Completed: improve retrieval parsing/ranking for weak eval cases and refresh retrieval/recommendation eval reports.
- Completed: add focused backend regression tests for `/recommend` citation integrity and model diversity.
- Completed: add provider selectors for embedding generation and recommendation generation while preserving deterministic local defaults.
- Completed: add OpenAI-backed structured recommendation provider behind the existing `/recommend` JSON contract, with deterministic fallback on missing key, API failure, or citation/schema validation failure.
- Completed: add selectable DeepSeek, Qwen, and Kimi recommendation providers through OpenAI-compatible Chat Completions with JSON-mode output, citation validation, and deterministic fallback.
- Completed: add repeatable live AI-provider validation tooling for `openai`, `deepseek`, `qwen`, and `kimi`, with missing-key skips and failure on deterministic fallback or invalid citations.
- Completed: pivot the canonical dataset from live listings to structured vehicle profiles.
- Completed: implement deterministic NZ valuation ranges for each ingested vehicle profile.
- Completed: replace listing-based `/retrieve` and `/recommend` contracts with vehicle-profile contracts.
- Completed: update the admin workbench and shortlist flow to compare 2-4 selected vehicle profiles.
- In progress: refresh broader project documentation and non-admin UX around the new profile-first scope.
- Pending: add deployment, screenshots, demo video, and public README polish.

## Accepted Decisions

- The project is a decision support system, not a generic chatbot.
- The MVP should be narrow before it is broad.
- Initial data scope should focus on Toyota, Mazda, and Honda.
- The first market is Auckland, New Zealand.
- Canonical seed data lives in `data/seed/`; archived raw listing export still lives in `data/raw/`.
- The active dataset is `data/seed/vehicle_profiles.jsonl`, not live market listings.
- The technical direction is FastAPI, Next.js, PostgreSQL, and pgvector.
- The first backend uses FastAPI with psycopg and PostgreSQL, not SQLite.
- Runtime database access uses SQLAlchemy ORM; raw SQL is reserved for migration files and minimal probes.
- The first retrieval endpoint started as non-LLM and non-embedding so the database contract could be validated before vector search and generation.
- The first embedding provider is a deterministic local hash embedding model so vector retrieval can be developed without external API keys. It is a development scaffold, not the final production embedding provider.
- The system must combine structured vehicle-profile filters with unstructured semantic retrieval.
- Deterministic valuation is part of the product contract for v1.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- No current implementation blocker for local hybrid retrieval, deterministic valuation, or deterministic recommendations.
- External embedding and LLM provider choice remains open before production-quality recommendation generation.

## Next Skill

Recommended next skill: `test-engineer` for live OpenAI-provider validation and prompt quality regression once an API key is available, followed by `frontend-implementer` for the decision workbench.

## Next Actions

1. Run `python3 apps/api/scripts/validate_ai_providers.py --fail-on-skip` after real provider keys are available.
2. Tune provider prompts against the eval cases if live generations expose wording, citation, or fallback issues.
3. Refresh remaining public docs and user-facing pages that still describe the old listing-first workflow.
4. Add deployment, screenshots, demo video, and public README polish after the UI can run end to end.
5. Add hosted-environment provider configuration notes once the API deployment target is chosen.

## Acceptance Gates

- Before implementation: product scope, schema, and API contracts are documented.
- Before frontend work: recommendation response JSON shape is stable enough for UI wiring.
- Before public release: README, architecture diagram, screenshots, demo script, eval report, and deployment links exist.
- Before LinkedIn posting: the app can run end to end and show citations, risk flags, and comparison output.

## Change Log

- Initial plan created from `documents/README.md`, `documents/used-car-rag-build-guide.md`, and `documents/linkedin-hr-pack.md`.
- Added canonical seed data layout, data preparation script, validation script, and updated project state after data validation.
- Added manual Honda Civic seed listing rows and cleared the listing coverage warning.
- Added Postgres/pgvector backend scaffold, initial schema, seed ingestion command, and first structured retrieval API.
- Verified Docker pgvector startup, migration, seed ingestion, `/health`, and `/retrieve` against local Postgres.
- Replaced runtime psycopg query calls with SQLAlchemy ORM models, sessions, ingestion, and retrieval queries.
- Added local chunk embedding generation, content-hash based skip behavior, pgvector semantic chunk retrieval, and `/retrieve` chunk debug output.
- Added HTTP retrieval eval runner, generated `documents/eval-report.md`, and improved brand, budget, body-type negation, running-cost, and premium-intent retrieval behavior based on the first baseline.
- Added deterministic citation-aware `/recommend`, model-diverse recommendation ranking, HTTP recommendation eval runner, and generated `documents/recommendation-eval-report.md`.
- Improved query context parsing, excluded-body-type handling, candidate model recall, low-risk ranking, risk-theme coverage, and `/recommend` citation regression tests.
- Added configurable provider selectors for local hash embeddings and deterministic recommendations, plus regression coverage for supported and unsupported provider names.
- Added OpenAI Responses API recommendation generation with Structured Outputs, local citation validation, deterministic fallback, and regression tests for success and fallback paths.
- Added DeepSeek, Qwen, and Kimi recommendation provider options through OpenAI-compatible Chat Completions with JSON-mode response handling and fallback regression tests.
- Added repeatable live AI-provider validation tooling; local execution skips providers without API keys and fails providers that fall back or produce invalid citations.
- Pivoted the backend and admin UI from live used-car listings to structured vehicle-profile retrieval with deterministic valuation.
