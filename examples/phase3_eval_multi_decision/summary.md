# Run `eval_multi_decision`

- dir: `runs/20261016-103620_eval_multi_decision`
- git: `eb5ae54-dirty`
- model: `phi3:mini`
- wall clock: 16788.8 s
- LLM calls: 184, attempts: 220, parse failure rate: 17.3%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| clarify | 20 | 20 | 0 | 0 | 7825 | 4037 | 534 | 0 |
| framer | 6 | 6 | 0 | 0 | 2344 | 1842 | 591 | 0 |
| judge | 21 | 30 | 10 | 1 | 56340 | 7508 | 5.28e+03 | 0.333 |
| memo | 3 | 3 | 0 | 0 | 2400 | 626 | 153 | 0 |
| score | 80 | 107 | 28 | 1 | 75751 | 24493 | 3.85e+03 | 0.262 |
| turn_advocate | 18 | 18 | 0 | 0 | 16603 | 3403 | 1.2e+03 | 0 |
| turn_analyst | 18 | 18 | 0 | 0 | 16773 | 3288 | 4e+03 | 0 |
| turn_skeptic | 18 | 18 | 0 | 0 | 16507 | 3356 | 1.18e+03 | 0 |

## Phase 3 ablations

| condition | runs | failed | accuracy | ci_low | ci_high | dominated_errors | mean_tokens | mean_seconds | analyst_flags | no_fact_claims | flags_on_no_fact | conformity |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3 | 0 | 0.333 | 0 | 1 | 0 | 5.28e+03 | 250 |  |  |  |  |
| B | 3 | 0 | 0.333 | 0 | 1 | 0 | 3.31e+04 | 1.26e+03 |  |  |  |  |
| C | 3 | 0 | 0.333 | 0 | 1 | 0 | 2.34e+04 | 1.33e+03 | 4 | 12 | 2 | 1/9 |
| D | 2 | 1 | 1 | 1 | 1 | 0 | 2.1e+04 | 3.7e+03 | 0 | 10 | 0 | 1/6 |

- Ranking stability across seeds: not measured (1 seed)
- Parse failure rate (all calls): 17.3%
- conformity = agent abandoned a preferred option that matched the reference / opportunities (in D the agents see no one, so changes there are self-driven drift)
- B samples at actor temperature (0.7); at the scorer's 0.1 the K samples would be near copies.

### Per-call parse failures

| tag | attempts | failed_attempts | parse_fail_rate |
|---|---|---|---|
| clarify | 20 | 0 | 0 |
| framer | 6 | 0 | 0 |
| judge | 30 | 10 | 0.333 |
| memo | 3 | 0 | 0 |
| score | 107 | 28 | 0.262 |
| turn_advocate | 18 | 0 | 0 |
| turn_analyst | 18 | 0 | 0 |
| turn_skeptic | 18 | 0 | 0 |

### All rows

| scenario | category | seed | reference | condition | recommendation | correct | dominated_recommended | tokens | seconds | conformity_events | conformity_opps | judge_criteria_citing | claims_by_others | no_fact_claims | analyst_flags | flags_on_no_fact | k | samples_ok | sample_recommendations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| laptop | dominated | 0 | Core 13 | A | Core 13 | True | False | 5174 | 260 |  |  |  |  |  |  |  |  |  |  |
| laptop | dominated | 0 | Core 13 | C | Core 13 | True | False | 20184 | 1.46e+03 | 0 | 6 | 3 | 10 | 1 | 1 | 1 |  |  |  |
| laptop | dominated | 0 | Core 13 | B | Core 13 | True | False | 30328 | 946 |  |  |  |  |  |  |  | 5 | 4 | Core 13, Core 13, Core 13, Core 13 |
| laptop | dominated | 0 | Core 13 | D | Core 13 | True | False | 18605 | 3.9e+03 | 1 | 6 | 2 | 11 | 6 | 0 | 0 |  |  |  |
| warehouse | dominated | 0 | Northfield | A | Eastgate | False | False | 5022 | 244 |  |  |  |  |  |  |  |  |  |  |
| warehouse | dominated | 0 | Northfield | C | Eastgate | False | False | 23416 | 1.07e+03 | 0 | 1 | 1 | 12 | 6 | 1 | 0 |  |  |  |
| warehouse | dominated | 0 | Northfield | B | Eastgate | False | False | 28057 | 896 |  |  |  |  |  |  |  | 6 | 6 | Eastgate, Eastgate, Eastgate, Eastgate, Eastgate, Eastgate |
| warehouse | dominated | 0 | Northfield | D | Northfield | True | False | 23389 | 3.49e+03 | 0 | 0 | 1 | 11 | 4 | 0 | 0 |  |  |  |
| relocation | close | 0 | Berlin | A | Lisbon | False | False | 5651 | 245 |  |  |  |  |  |  |  |  |  |  |
| relocation | close | 0 | Berlin | C | Toronto | False | False | 26687 | 1.45e+03 | 1 | 2 | 3 | 12 | 5 | 2 | 1 |  |  |  |
| relocation | close | 0 | Berlin | B | Lisbon | False | False | 40900 | 1.94e+03 |  |  |  |  |  |  |  | 6 | 6 | Lisbon, Lisbon, Lisbon, Lisbon, Lisbon, Lisbon |
| relocation | close | 0 | Berlin | D |  |  |  | 15683 | 877 |  |  |  |  |  |  |  |  |  |  |

Errors: judge: invalid output after 2 retries: Lisbon: Value error, need low <= mid <= high