# Recommendation Eval Report

## Run Metadata

- Generated at: `2026-04-24T09:21:34.175320+00:00`
- API URL: `http://127.0.0.1:8011`
- Seed data: `data/seed`
- Recommend limit: `3`
- Recommendation mode: `deterministic_ranker_with_citations`
- Embedding model: `local-hash-embedding-v1`

## Summary

- Cases: 20
- Average model recall: 92.08%
- Average risk theme recall: 90.42%
- Average citation score: 100.00%
- Cases with full citations: 20/20
- Average recommendations per case: 2.95

## Weakest Cases

### eval-014

- Model recall: 50.00%
- Risk theme recall: 60.00%
- Citation score: 100.00%
- Missed models: Toyota Prius, Honda Civic, Mazda3
- Missed risk themes: older age, safety equipment variation
- Citation failures: none

### eval-012

- Model recall: 75.00%
- Risk theme recall: 80.00%
- Citation score: 100.00%
- Missed models: Honda Fit
- Missed risk themes: wear items
- Citation failures: none

### eval-009

- Model recall: 66.67%
- Risk theme recall: 100.00%
- Citation score: 100.00%
- Missed models: Toyota Prius
- Missed risk themes: none
- Citation failures: none

### eval-002

- Model recall: 100.00%
- Risk theme recall: 75.00%
- Citation score: 100.00%
- Missed models: none
- Missed risk themes: visibility
- Citation failures: none

### eval-005

- Model recall: 100.00%
- Risk theme recall: 75.00%
- Citation score: 100.00%
- Missed models: none
- Missed risk themes: fuel cost
- Citation failures: none

## Case Details

### eval-001

- Query: I need a reliable car under $12,000 for commuting in Auckland.
- Expected models: Toyota Aqua, Honda Fit, Mazda2
- Recommended models: Honda Fit, Mazda2, Toyota Aqua
- Model hits: Toyota Aqua, Honda Fit, Mazda2
- Risk theme hits: high mileage, service history, maintenance cost, accident repair
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-002

- Query: Which of these is better for city driving: Toyota Aqua, Honda Fit, or Mazda2?
- Expected models: Toyota Aqua, Honda Fit, Mazda2
- Recommended models: Honda Fit, Mazda2, Toyota Aqua
- Model hits: Toyota Aqua, Honda Fit, Mazda2
- Risk theme hits: small car practicality, service history, used import condition
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-003

- Query: I want a family SUV in Auckland and my budget is around $20,000.
- Expected models: Toyota RAV4, Honda HR-V, Mazda CX-5
- Recommended models: Honda HR-V, Mazda CX-5, Toyota RAV4
- Model hits: Toyota RAV4, Honda HR-V, Mazda CX-5
- Risk theme hits: service history, tyres, brakes, accident repair, running cost
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-004

- Query: Is a used Toyota Prius a good choice for Uber-style driving in Auckland?
- Expected models: Toyota Prius
- Recommended models: Toyota Prius
- Model hits: Toyota Prius
- Risk theme hits: high mileage, hybrid system condition, service history, seat wear, brake wear
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 6

### eval-005

- Query: I only want Honda. Which Honda model is most practical for daily commuting and grocery runs?
- Expected models: Honda Fit, Honda Civic, Honda HR-V
- Recommended models: Honda Civic, Honda Fit, Honda HR-V
- Model hits: Honda Fit, Honda Civic, Honda HR-V
- Risk theme hits: service history, cargo practicality, maintenance cost
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-006

- Query: Between Mazda3 and Honda Civic, which is the better first car for a new driver?
- Expected models: Mazda3, Honda Civic
- Recommended models: Honda Civic, Mazda3
- Model hits: Mazda3, Honda Civic
- Risk theme hits: insurance cost, service history, accident repair, tyre condition
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 9

### eval-007

- Query: What should I check before buying a used Toyota Aqua in Auckland?
- Expected models: Toyota Aqua
- Recommended models: Toyota Aqua
- Model hits: Toyota Aqua
- Risk theme hits: service history, accident repair, battery or hybrid condition, tyres, brakes
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 6

### eval-008

- Query: I drive mostly short distances. Should I get a Honda Fit or Toyota Aqua?
- Expected models: Honda Fit, Toyota Aqua
- Recommended models: Honda Fit, Toyota Aqua
- Model hits: Honda Fit, Toyota Aqua
- Risk theme hits: interior space, service history, small car comfort
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 9

### eval-009

- Query: I need something comfortable for highway driving between Auckland and Hamilton. Budget under $18,000.
- Expected models: Honda Civic, Mazda3, Toyota Prius
- Recommended models: Honda Civic, Mazda3, Toyota Aqua
- Model hits: Honda Civic, Mazda3
- Risk theme hits: road noise, seat comfort, service history, tyres, brake condition
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-010

- Query: Which is likely to be cheaper to own: Mazda CX-5 or Toyota RAV4?
- Expected models: Mazda CX-5, Toyota RAV4
- Recommended models: Mazda CX-5, Toyota RAV4
- Model hits: Mazda CX-5, Toyota RAV4
- Risk theme hits: fuel cost, maintenance cost, tyres, service intervals, repair cost
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 9

### eval-011

- Query: I have two adults and one child. Is Honda HR-V big enough for everyday family use?
- Expected models: Honda HR-V
- Recommended models: Honda HR-V
- Model hits: Honda HR-V
- Risk theme hits: rear seat space, boot space, child seat practicality, service history
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 2 / 5

### eval-012

- Query: I care most about low running costs. Which should I shortlist: Toyota Aqua, Prius, Fit, or Mazda2?
- Expected models: Toyota Aqua, Toyota Prius, Honda Fit, Mazda2
- Recommended models: Mazda2, Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Toyota Prius, Mazda2
- Risk theme hits: fuel cost, maintenance cost, service history, hybrid-related checks
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-013

- Query: What are the main risks when buying a high-mileage Mazda3?
- Expected models: Mazda3
- Recommended models: Mazda3
- Model hits: Mazda3
- Risk theme hits: high mileage, service history, suspension wear, brakes, transmission behaviour, oil leaks
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 6

### eval-014

- Query: I want a used car under $10,000 and I do not want an SUV. What are the safer choices from Toyota, Honda, and Mazda?
- Expected models: Toyota Aqua, Toyota Prius, Honda Fit, Honda Civic, Mazda2, Mazda3
- Recommended models: Honda Fit, Mazda2, Toyota Aqua
- Model hits: Toyota Aqua, Honda Fit, Mazda2
- Risk theme hits: high mileage, service history, accident repair
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-015

- Query: Is Mazda2 too small if I sometimes carry a child and shopping bags?
- Expected models: Mazda2
- Recommended models: Mazda2
- Model hits: Mazda2
- Risk theme hits: rear seat space, boot space, child seat fit, small car comfort
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 6

### eval-016

- Query: I want the most reliable Toyota hybrid for daily use. Should I look at Aqua or Prius?
- Expected models: Toyota Aqua, Toyota Prius
- Recommended models: Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Toyota Prius
- Risk theme hits: service history, hybrid system condition, high mileage, accident repair
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 9

### eval-017

- Query: Which of the listed Mazda and Honda models are better for people who want a slightly more premium feel?
- Expected models: Mazda3, Mazda CX-5, Honda Civic, Honda HR-V
- Recommended models: Honda Civic, Mazda CX-5, Mazda3
- Model hits: Mazda3, Mazda CX-5, Honda Civic
- Risk theme hits: trim differences, feature variation by year, service history, used condition
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-018

- Query: I do not know much about cars. Give me the simplest low-risk used car choice for Auckland from these brands.
- Expected models: Toyota Aqua, Honda Fit, Mazda3
- Recommended models: Honda Fit, Mazda3, Toyota Aqua
- Model hits: Toyota Aqua, Honda Fit, Mazda3
- Risk theme hits: service history, pre-purchase inspection, maintenance cost, accident repair, avoid neglected examples
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12

### eval-019

- Query: For a used CX-5, what inspection points matter most before purchase?
- Expected models: Mazda CX-5
- Recommended models: Mazda CX-5
- Model hits: Mazda CX-5
- Risk theme hits: service history, suspension, tyres, brakes, accident repair, warning lights
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 6

### eval-020

- Query: I want a hatchback that is cheap to run and easy to park in Auckland. Which models should I compare?
- Expected models: Toyota Aqua, Honda Fit, Mazda2, Toyota Prius
- Recommended models: Honda Fit, Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Honda Fit, Toyota Prius
- Risk theme hits: fuel economy, service history, small-car practicality, used condition, parking damage
- Citation score: 100.00%
- Citation failures: none
- Recommendations / evidence: 3 / 12
