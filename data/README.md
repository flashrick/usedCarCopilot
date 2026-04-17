# Data README

This directory contains the early MVP dataset for AI Used Car Decision Copilot.

## Canonical Seed Data

Use these files for ingestion, retrieval tests, and future API work:

- `data/seed/listings.jsonl`
- `data/seed/knowledge_sources.jsonl`
- `data/seed/eval_cases.json`

## Raw Data

- `data/raw/turners_listings.jsonl` keeps the raw Turners listing export used to generate the normalized seed listing data.

## Working Notes

- `data/listing.md` describes the intended listing shape and data coverage target.
- `data/car_model_data.md` is an earlier human-readable knowledge draft. The canonical machine-readable version is `data/seed/knowledge_sources.jsonl`.

## Scripts

Generate normalized seed listings from the raw Turners export:

```bash
python3 scripts/prepare_seed_data.py
```

Validate listings, knowledge sources, and eval cases:

```bash
python3 scripts/validate_seed_data.py
```

## Current Data Coverage

Seed listings currently cover:

- Honda Fit
- Honda Civic
- Honda HR-V
- Mazda CX-5
- Mazda Mazda2
- Mazda Mazda3
- Toyota Aqua
- Toyota Prius
- Toyota RAV4

Seed knowledge currently covers:

- Honda Civic
- Honda Fit
- Honda HR-V
- Mazda CX-5
- Mazda Mazda2
- Mazda Mazda3
- Toyota Aqua
- Toyota Prius
- Toyota RAV4

Current note:

- Honda Civic listing rows are manual seed rows, not raw Turners export rows.
