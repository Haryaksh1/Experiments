# Run `eval_decision`

- dir: `runs/20261015-205051_eval_decision`
- git: `9ac9391-dirty`
- model: `phi3:mini`
- wall clock: 8759.7 s
- LLM calls: 88, attempts: 92, parse failure rate: 5.4%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| clarify | 10 | 10 | 0 | 0 | 3938 | 1789 | 872 | 0 |
| memo | 9 | 9 | 0 | 0 | 7112 | 1927 | 718 | 0 |
| score | 69 | 73 | 5 | 1 | 50780 | 16656 | 7.17e+03 | 0.0685 |

## Phase 1 results

- Scenarios: 10, runs: 18, failed runs: 1
- Agreement with reference (seed 0): 78% (95% bootstrap CI 44%-100%, n=9)
- Dominated option recommended: 0 of 17 runs
- Reference-dominated option also dominated in the model's scores: 5 of 5 scenarios
- Top-1 stable across seeds: 4 of 4 scenarios; full ranking stable: 4 of 4
- Parse failure rate (failed attempts / attempts): 5.4%
- Time per scenario, full run: 498 s; extra-seed re-score: 522 s

### Agreement by category

| category | mean | count |
|---|---|---|
| clear | 1 | 1 |
| close | 0.667 | 3 |
| dominated | 0.8 | 5 |

### Seed stability

| scenario | seeds | top1_stable | ranking_stable | recommendations |
|---|---|---|---|---|
| heating | 3 | True | True | Heat pump, Heat pump, Heat pump |
| job_offer | 3 | True | True | Bank, Bank, Bank |
| laptop | 3 | True | True | Core 13, Core 13, Core 13 |
| venue | 3 | True | True | Hotel Central, Hotel Central, Hotel Central |

### All runs

| scenario | category | seed | reference | recommendation | correct | dominated_recommended | ref_dominated_detected | ranking | margin | seconds | error |
|---|---|---|---|---|---|---|---|---|---|---|---|
| laptop | dominated | 0 | Core 13 | Core 13 | True | False | True | Core 13 > Aero 14 > Bolt 15 | 0.8 | 637 |  |
| laptop | dominated | 1 | Core 13 | Core 13 | True | False | True | Core 13 > Aero 14 > Bolt 15 | 1.54 | 809 |  |
| laptop | dominated | 2 | Core 13 | Core 13 | True | False | True | Core 13 > Aero 14 > Bolt 15 | 1.5 | 321 |  |
| heating | close | 0 | Heat pump | Heat pump | True | False |  | Heat pump > Gas boiler > Pellet stove | 0.65 | 642 |  |
| heating | close | 1 | Heat pump | Heat pump | True | False |  | Heat pump > Gas boiler > Pellet stove | 1.12 | 439 |  |
| heating | close | 2 | Heat pump | Heat pump | True | False |  | Heat pump > Gas boiler > Pellet stove | 0.48 | 362 |  |
| job_offer | clear | 0 | Bank | Bank | True | False |  | Bank > University > Startup | 1.47 | 654 |  |
| job_offer | clear | 1 | Bank | Bank | True | False |  | Bank > University > Startup | 0.32 | 478 |  |
| job_offer | clear | 2 | Bank | Bank | True | False |  | Bank > University > Startup | 2.18 | 280 |  |
| venue | close | 0 | Hotel Central | Hotel Central | True | False |  | Hotel Central > Expo Hall > University Campus | 1.04 | 962 |  |
| venue | close | 1 | Hotel Central | Hotel Central | True | False |  | Hotel Central > Expo Hall > University Campus | 1 | 759 |  |
| venue | close | 2 | Hotel Central | Hotel Central | True | False |  | Hotel Central > Expo Hall > University Campus | 1.24 | 728 |  |
| supplier | dominated | 0 | Supplier A | Supplier A | True | False | True | Supplier A > Supplier B > Supplier C | 2 | 862 |  |
| framework | dominated | 0 | Django | Django | True | False | True | Django > Express > Rails | 0.12 | 181 |  |
| crm | dominated | 0 | CRM-One |  |  |  |  |  |  |  | score: invalid output after 2 retries: CRM-One: Value error, need low <= mid <= high; Pipedrop: Value error, need low <= mid <= high |
| marketing | dominated | 0 | Search ads | Search ads | True | False | True | Search ads > Trade shows > Influencers | 0.55 | 178 |  |
| warehouse | dominated | 0 | Northfield | Eastgate | False | False | True | Eastgate > Northfield > Riverside | 0.67 | 170 |  |
| relocation | close | 0 | Berlin | Lisbon | False | False |  | Lisbon > Berlin > Toronto | 1.03 | 197 |  |
