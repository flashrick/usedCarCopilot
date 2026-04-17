# Data And Evaluation Plan

## Data Goal

The MVP needs enough data to demonstrate structured filtering, semantic retrieval, grounded generation, and meaningful comparison. It does not need large-scale coverage.

Quality matters more than size for the first version.

## Data Types

### Structured Listings

Required fields:

- listing id
- title
- brand
- model
- trim
- year
- price
- mileage
- transmission
- fuel type
- seller type
- location
- listing URL or source label
- seller description

Useful derived fields:

- price band
- mileage band
- age
- budget fit score
- mileage risk level
- usage fit tags

### Knowledge Sources

Knowledge sources should cover:

- model reliability notes
- common faults
- maintenance cost guidance
- owner review snippets
- buying guide advice
- inspection checklist items

Each source should keep:

- source id
- title
- source type
- URL or local source label
- publish date if available
- extracted text
- credibility notes if useful

### Document Chunks

Each chunk should keep:

- chunk id
- source id
- text
- section title if available
- source type
- brand/model tags
- embedding vector
- embedding model version

## First Dataset Recommendation

Start with a hand-checkable dataset:

- 30-60 listings
- 50-100 knowledge chunks
- Toyota, Mazda, and Honda only
- One local market or demo city
- A mix of safe, borderline, and risky listings

This is enough to make ranking and evaluation meaningful without spending the first weeks on scraping infrastructure.

## Ingestion Steps

1. Define `listings.csv` or `listings.json`.
2. Define `knowledge_sources.jsonl`.
3. Validate required fields.
4. Normalize brand, model, price, mileage, year, and fuel type.
5. Chunk unstructured knowledge.
6. Generate embeddings.
7. Store listing records, source records, chunks, and vectors.
8. Run a small smoke retrieval query.

## Evaluation Dataset

Create at least 20 eval cases.

Each case should include:

- user query
- expected structured filters
- expected useful brands or models
- expected risk themes
- expected evidence source types
- notes about what a good answer should avoid

Example:

```json
{
  "id": "eval-001",
  "query": "I need a reliable car under $12,000 for commuting and occasional weekend trips.",
  "expected_filters": {
    "max_price": 12000,
    "usage": "commute"
  },
  "expected_risk_themes": ["high mileage", "maintenance cost", "service history"],
  "expected_evidence_types": ["listing", "maintenance", "review"]
}
```

## Evaluation Metrics

### Retrieval

- Did top-k chunks contain relevant evidence?
- Did retrieval include both listing facts and knowledge snippets?
- Were irrelevant chunks low enough in the ranking?
- Did filters remove obviously unsuitable listings?

### Generation

- Were recommendation reasons supported by evidence?
- Were citations attached to important claims?
- Did the answer avoid inventing facts not found in context?
- Was JSON output valid and renderable?

### Product Usefulness

- Can a buyer understand the trade-off?
- Are risk flags specific enough to act on?
- Are next steps practical?
- Does the comparison make the decision easier?

## Eval Report Structure

`eval_report.md` should include:

- date and commit
- dataset version
- model and embedding model
- retrieval settings
- pass/fail summary
- examples of strong outputs
- examples of weak outputs
- next fixes

## Release Gate

Before this project is presented publicly, at least one eval report should exist and the README should summarize the main evaluation findings honestly.

