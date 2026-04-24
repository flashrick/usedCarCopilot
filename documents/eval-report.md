# Retrieval Eval Report

## Run Metadata

- Generated at: `2026-04-24T09:21:33.907097+00:00`
- API URL: `http://127.0.0.1:8011`
- Seed data: `data/seed`
- Retrieve limit: `5`
- Embedding model: `local-hash-embedding-v1`

## Summary

- Cases: 20
- Average model recall: 100.00%
- Average risk theme recall: 87.92%
- Average filter recall: 94.17%
- Embedding-enabled cases: 20/20
- Cases with semantic chunks: 20/20
- Perfect model coverage cases: 20/20
- Perfect risk-theme coverage cases: 13/20

## Weakest Cases

### eval-017

- Model recall: 100.00%
- Risk theme recall: 25.00%
- Filter recall: 100.00%
- Missed models: none
- Missed risk themes: trim differences, feature variation by year, used condition

### eval-002

- Model recall: 100.00%
- Risk theme recall: 50.00%
- Filter recall: 100.00%
- Missed models: none
- Missed risk themes: visibility, used import condition

### eval-020

- Model recall: 100.00%
- Risk theme recall: 60.00%
- Filter recall: 100.00%
- Missed models: none
- Missed risk themes: used condition, parking damage

### eval-008

- Model recall: 100.00%
- Risk theme recall: 100.00%
- Filter recall: 66.67%
- Missed models: none
- Missed risk themes: none

### eval-010

- Model recall: 100.00%
- Risk theme recall: 100.00%
- Filter recall: 66.67%
- Missed models: none
- Missed risk themes: none

## Case Details

### eval-001

- Query: I need a reliable car under $12,000 for commuting in Auckland.
- Expected models: Toyota Aqua, Honda Fit, Mazda2
- Retrieved models: Honda Civic, Honda Fit, Honda HR-V, Mazda CX-5, Mazda2, Mazda3, Toyota Aqua, Toyota Prius, Toyota RAV4
- Model hits: Toyota Aqua, Honda Fit, Mazda2
- Risk theme hits: high mileage, service history, maintenance cost, accident repair
- Filter hits: max_price, usage, location, priority
- Listings / knowledge / chunks: 5 / 15 / 15

### eval-002

- Query: Which of these is better for city driving: Toyota Aqua, Honda Fit, or Mazda2?
- Expected models: Toyota Aqua, Honda Fit, Mazda2
- Retrieved models: Honda Fit, Mazda2, Toyota Aqua
- Model hits: Toyota Aqua, Honda Fit, Mazda2
- Risk theme hits: small car practicality, service history
- Filter hits: usage, compare_models, priority
- Listings / knowledge / chunks: 5 / 9 / 9

### eval-003

- Query: I want a family SUV in Auckland and my budget is around $20,000.
- Expected models: Toyota RAV4, Honda HR-V, Mazda CX-5
- Retrieved models: Honda HR-V, Mazda CX-5, Toyota RAV4
- Model hits: Toyota RAV4, Honda HR-V, Mazda CX-5
- Risk theme hits: service history, tyres, brakes, accident repair, running cost
- Filter hits: body_type, usage, location, target_price
- Listings / knowledge / chunks: 5 / 9 / 9

### eval-004

- Query: Is a used Toyota Prius a good choice for Uber-style driving in Auckland?
- Expected models: Toyota Prius
- Retrieved models: Toyota Prius
- Model hits: Toyota Prius
- Risk theme hits: high mileage, hybrid system condition, service history, seat wear, brake wear
- Filter hits: model, usage, location
- Listings / knowledge / chunks: 5 / 3 / 3

### eval-005

- Query: I only want Honda. Which Honda model is most practical for daily commuting and grocery runs?
- Expected models: Honda Fit, Honda Civic, Honda HR-V
- Retrieved models: Honda Civic, Honda Fit, Honda HR-V
- Model hits: Honda Fit, Honda Civic, Honda HR-V
- Risk theme hits: service history, cargo practicality, fuel cost, maintenance cost
- Filter hits: brand, usage, secondary_usage, priority
- Listings / knowledge / chunks: 5 / 9 / 9

### eval-006

- Query: Between Mazda3 and Honda Civic, which is the better first car for a new driver?
- Expected models: Mazda3, Honda Civic
- Retrieved models: Honda Civic, Mazda3
- Model hits: Mazda3, Honda Civic
- Risk theme hits: insurance cost, service history, accident repair, tyre condition
- Filter hits: compare_models, usage, driver_profile
- Listings / knowledge / chunks: 5 / 6 / 6

### eval-007

- Query: What should I check before buying a used Toyota Aqua in Auckland?
- Expected models: Toyota Aqua
- Retrieved models: Toyota Aqua
- Model hits: Toyota Aqua
- Risk theme hits: service history, accident repair, battery or hybrid condition, tyres, brakes
- Filter hits: model, location, ownership_stage, intent
- Listings / knowledge / chunks: 4 / 3 / 3

### eval-008

- Query: I drive mostly short distances. Should I get a Honda Fit or Toyota Aqua?
- Expected models: Honda Fit, Toyota Aqua
- Retrieved models: Honda Fit, Toyota Aqua
- Model hits: Honda Fit, Toyota Aqua
- Risk theme hits: fuel economy, interior space, service history, small car comfort
- Filter hits: compare_models, priority
- Listings / knowledge / chunks: 5 / 6 / 6

### eval-009

- Query: I need something comfortable for highway driving between Auckland and Hamilton. Budget under $18,000.
- Expected models: Honda Civic, Mazda3, Toyota Prius
- Retrieved models: Honda Civic, Honda Fit, Honda HR-V, Mazda CX-5, Mazda2, Mazda3, Toyota Aqua, Toyota Prius, Toyota RAV4
- Model hits: Honda Civic, Mazda3, Toyota Prius
- Risk theme hits: road noise, seat comfort, service history, tyres, brake condition
- Filter hits: max_price, usage, route_profile, location
- Listings / knowledge / chunks: 5 / 15 / 15

### eval-010

- Query: Which is likely to be cheaper to own: Mazda CX-5 or Toyota RAV4?
- Expected models: Mazda CX-5, Toyota RAV4
- Retrieved models: Mazda CX-5, Toyota RAV4
- Model hits: Mazda CX-5, Toyota RAV4
- Risk theme hits: fuel cost, maintenance cost, tyres, service intervals, repair cost
- Filter hits: compare_models, intent
- Listings / knowledge / chunks: 5 / 6 / 6

### eval-011

- Query: I have two adults and one child. Is Honda HR-V big enough for everyday family use?
- Expected models: Honda HR-V
- Retrieved models: Honda HR-V
- Model hits: Honda HR-V
- Risk theme hits: rear seat space, boot space, child seat practicality, service history
- Filter hits: model, usage, household_size, priority
- Listings / knowledge / chunks: 2 / 3 / 3

### eval-012

- Query: I care most about low running costs. Which should I shortlist: Toyota Aqua, Prius, Fit, or Mazda2?
- Expected models: Toyota Aqua, Toyota Prius, Honda Fit, Mazda2
- Retrieved models: Honda Fit, Mazda2, Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Toyota Prius, Honda Fit, Mazda2
- Risk theme hits: fuel cost, maintenance cost, service history, wear items, hybrid-related checks
- Filter hits: compare_models, priority
- Listings / knowledge / chunks: 5 / 9 / 12

### eval-013

- Query: What are the main risks when buying a high-mileage Mazda3?
- Expected models: Mazda3
- Retrieved models: Mazda3
- Model hits: Mazda3
- Risk theme hits: high mileage, service history, suspension wear, brakes, transmission behaviour, oil leaks
- Filter hits: model, intent, mileage_band
- Listings / knowledge / chunks: 5 / 3 / 3

### eval-014

- Query: I want a used car under $10,000 and I do not want an SUV. What are the safer choices from Toyota, Honda, and Mazda?
- Expected models: Toyota Aqua, Toyota Prius, Honda Fit, Honda Civic, Mazda2, Mazda3
- Retrieved models: Honda Civic, Honda Fit, Mazda2, Mazda3, Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Toyota Prius, Honda Fit, Honda Civic, Mazda2, Mazda3
- Risk theme hits: older age, high mileage, service history, accident repair
- Filter hits: max_price, exclude_body_type, brands, priority
- Listings / knowledge / chunks: 5 / 15 / 15

### eval-015

- Query: Is Mazda2 too small if I sometimes carry a child and shopping bags?
- Expected models: Mazda2
- Retrieved models: Mazda2
- Model hits: Mazda2
- Risk theme hits: rear seat space, boot space, child seat fit, small car comfort
- Filter hits: model, usage, household_size
- Listings / knowledge / chunks: 3 / 3 / 3

### eval-016

- Query: I want the most reliable Toyota hybrid for daily use. Should I look at Aqua or Prius?
- Expected models: Toyota Aqua, Toyota Prius
- Retrieved models: Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Toyota Prius
- Risk theme hits: service history, hybrid system condition, high mileage, accident repair
- Filter hits: brand, fuel_type, compare_models, usage, priority
- Listings / knowledge / chunks: 5 / 6 / 6

### eval-017

- Query: Which of the listed Mazda and Honda models are better for people who want a slightly more premium feel?
- Expected models: Mazda3, Mazda CX-5, Honda Civic, Honda HR-V
- Retrieved models: Honda Civic, Honda Fit, Honda HR-V, Mazda CX-5, Mazda2, Mazda3
- Model hits: Mazda3, Mazda CX-5, Honda Civic, Honda HR-V
- Risk theme hits: service history
- Filter hits: brands, priority
- Listings / knowledge / chunks: 5 / 15 / 15

### eval-018

- Query: I do not know much about cars. Give me the simplest low-risk used car choice for Auckland from these brands.
- Expected models: Toyota Aqua, Honda Fit, Mazda3
- Retrieved models: Honda Civic, Honda Fit, Honda HR-V, Mazda CX-5, Mazda2, Mazda3, Toyota Aqua, Toyota Prius, Toyota RAV4
- Model hits: Toyota Aqua, Honda Fit, Mazda3
- Risk theme hits: service history, pre-purchase inspection, maintenance cost, accident repair, avoid neglected examples
- Filter hits: location, priority, user_profile, brands
- Listings / knowledge / chunks: 5 / 15 / 15

### eval-019

- Query: For a used CX-5, what inspection points matter most before purchase?
- Expected models: Mazda CX-5
- Retrieved models: Mazda CX-5
- Model hits: Mazda CX-5
- Risk theme hits: service history, suspension, tyres, brakes, accident repair, warning lights
- Filter hits: model, ownership_stage, intent
- Listings / knowledge / chunks: 5 / 3 / 3

### eval-020

- Query: I want a hatchback that is cheap to run and easy to park in Auckland. Which models should I compare?
- Expected models: Toyota Aqua, Honda Fit, Mazda2, Toyota Prius
- Retrieved models: Honda Fit, Mazda2, Mazda3, Toyota Aqua, Toyota Prius
- Model hits: Toyota Aqua, Honda Fit, Mazda2, Toyota Prius
- Risk theme hits: fuel economy, service history, small-car practicality
- Filter hits: body_type, priority, secondary_priority, location
- Listings / knowledge / chunks: 5 / 15 / 15
