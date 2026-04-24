# PLANS.md

## Goal

Build an AI Used Car Decision Copilot that demonstrates real AI engineering ability through RAG, hybrid retrieval, structured filtering, citation-grounded generation, evaluation, and a deployable API/UI experience.

## Current Stage

Stage: Live AI provider validation workflow added.

The repository now has planning documents, seed data, and the first FastAPI/PostgreSQL backend scaffold. The schema includes pgvector support and tables for listings, knowledge sources, document chunks, chunk embeddings, eval cases, ingestion runs, and request logs. Runtime database access uses SQLAlchemy ORM sessions and mapped records. Seed ingestion, local deterministic chunk embedding generation, pgvector semantic retrieval, deterministic citation-aware recommendation generation, provider selectors for embeddings and recommendations, selectable AI recommendation providers with deterministic fallback, retrieval/recommendation eval runners, live-provider validation tooling, and focused backend regression tests have been run successfully against a local pgvector Postgres container.

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
- In progress: build ingestion and embedding pipeline. Seed ingestion, local embedding generation, and embedding provider selection are implemented and verified; external provider implementation is pending.
- In progress: build retrieval API and debug output. Structured retrieval and pgvector semantic chunk retrieval are implemented and service-verified.
- In progress: add evaluation workflow and reporting. Retrieval and deterministic recommendation eval reports exist; LLM generation eval is pending.
- In progress: build recommendation API with citation-aware JSON output. Deterministic ranked recommendations, recommendation provider selection, OpenAI-backed structured generation, and OpenAI-compatible DeepSeek/Qwen/Kimi generation are implemented; live API-key validation and prompt quality tuning are pending.
- Pending: build decision-workbench UI.
- Pending: add deployment, screenshots, demo video, and public README polish.

## Accepted Decisions

- The project is a decision support system, not a generic chatbot.
- The MVP should be narrow before it is broad.
- Initial data scope should focus on Toyota, Mazda, and Honda.
- The first market is Auckland, New Zealand.
- The first listing source is Turners data normalized into `data/seed/listings.jsonl`.
- Canonical seed data lives in `data/seed/`; raw listing export lives in `data/raw/`.
- The technical direction is FastAPI, Next.js, PostgreSQL, and pgvector.
- The first backend uses FastAPI with psycopg and PostgreSQL, not SQLite.
- Runtime database access uses SQLAlchemy ORM; raw SQL is reserved for migration files and minimal probes.
- The first retrieval endpoint started as non-LLM and non-embedding so the database contract could be validated before vector search and generation.
- The first embedding provider is a deterministic local hash embedding model so vector retrieval can be developed without external API keys. It is a development scaffold, not the final production embedding provider.
- The system must combine structured listing filters with unstructured semantic retrieval.
- Recommendation claims must be grounded with evidence citations.
- Evaluation is part of the MVP, not a later optional polish step.

## Open Questions

- Should the project use OpenAI, Anthropic, or a provider-abstracted LLM interface for the first build?
- What deployment target should be chosen for the API: Render, Railway, Fly.io, or Azure App Service?
- Should the public README and demo be written mainly in English, Chinese, or bilingual format?

## Blockers

- No current implementation blocker for local hybrid retrieval or deterministic recommendations.
- External embedding and LLM provider choice remains open before production-quality recommendation generation.

## Next Skill

Recommended next skill: `test-engineer` for live OpenAI-provider validation and prompt quality regression once an API key is available, followed by `frontend-implementer` for the decision workbench.

## Next Actions

1. Run `python3 apps/api/scripts/validate_ai_providers.py --fail-on-skip` after real provider keys are available.
2. Tune provider prompts against the 20 eval cases if live generations expose wording, citation, or fallback issues.
3. Continue frontend decision-workbench integration using the stable `/retrieve` and `/recommend` response contracts.
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
