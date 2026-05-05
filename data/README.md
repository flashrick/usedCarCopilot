# Data README

This directory contains the early MVP dataset for AI Used Car Decision Copilot.

## Canonical Seed Data

Use these files for ingestion, retrieval tests, and future API work:

- `data/seed/vehicle_profiles.jsonl`
- `data/seed/knowledge_sources.jsonl`
- `data/seed/eval_cases.json`

## Raw Data

- `data/raw/turners_listings.jsonl` is archived reference data from the earlier listing-based direction. It is no longer part of canonical ingestion.

## Working Notes

- `data/listing.md` is an archived note from the earlier listing-based direction.
- `data/car_model_data.md` is an earlier human-readable knowledge draft. The canonical machine-readable version is `data/seed/knowledge_sources.jsonl`.

## Scripts

Validate vehicle profiles, knowledge sources, and eval cases:

```bash
python3 scripts/validate_seed_data.py
```

## Current Data Coverage

Seed vehicle profiles currently cover:

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

The profile dataset is deliberately variant-level. Each row is a concrete candidate profile with trim, powertrain, fuel economy, comfort/NVH notes, maintenance-cost band, and deterministic valuation fields computed at ingestion time.
