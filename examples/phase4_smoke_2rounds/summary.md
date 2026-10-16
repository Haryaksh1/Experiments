# Run `simulate`

- dir: `runs/20261016-151727_simulate`
- git: `18ea0eb`
- model: `phi3:mini`
- wall clock: 586.8 s
- LLM calls: 30, attempts: 30, parse failure rate: 0.0%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| builder | 1 | 1 | 0 | 0 | 192 | 362 | 36.2 | 0 |
| chat | 6 | 6 | 0 | 0 | 2947 | 231 | 131 | 0 |
| decide | 6 | 6 | 0 | 0 | 3347 | 257 | 156 | 0 |
| importance | 12 | 12 | 0 | 0 | 3107 | 281 | 125 | 0 |
| observer | 1 | 1 | 0 | 0 | 352 | 365 | 46 | 0 |
| observer_report | 1 | 1 | 0 | 0 | 708 | 172 | 42.7 | 0 |
| plan | 3 | 3 | 0 | 0 | 1140 | 138 | 49.2 | 0 |

## Condition: single (chat on)

| round | Jasmine | Raj | Lucy | Jasmine promise | Raj promise | Lucy promise |
|---|---|---|---|---|---|---|
| 1 | 10 | 8 | 8 | -1 | 5 | -1 |
| 2 | 10 | 10 | 7 | -1 | -1 | 9 |

- mean contribution 8.83, trend 0.333 per round, first 8.67 -> last 9.00
- total payoffs: {'Jasmine': 26.5, 'Raj': 28.5, 'Lucy': 31.5}
- private fact: {'owner': 'Jasmine', 'owner_first_mention': None, 'others_first_mention': {'Raj': None, 'Lucy': None}, 'spread_to': [], 'knowledge_before_exposure': []}
- promises: {'promises': 2, 'kept': 1, 'broken': 1, 'kept_rate': 0.5, 'mean_gap_contribution_minus_promise': 0.5, 'broken_list': ['R2 Lucy: promised 9, gave 7']}
- reflections: {'Jasmine': 0, 'Raj': 0, 'Lucy': 0}
- misstatements listed by the Observer: [{'round': 1, 'agent': 'Raj', 'statement': 'I dream of a vibrant community garden where kids can play and families bond every day.', 'why': "The statement does not reveal Raj's knowledge about the city council grant."}, {'round': 2, 'agent': 'Lucy', 'statement': "Let's grow our dream garden into a thriving hub for unique baked treasures!", 'why': "The statement does not reveal Lucy's knowledge about the city council grant."}, {'round': 1, 'agent': 'Jasmine', 'statement': 'Looking forward to seeing our garden grow and sharing its beauty through my designs!', 'why': "The statement does not reveal Jasmine's knowledge about the city council grant."}, {'round': 2, 'agent': 'Raj', 'statement': "Let's add more greenery!", 'why': "This statement suggests Raj might be unaware of Jasmine's private knowledge about the city council grant."}, {'round': 2, 'agent': 'Lucy', 'statement': "Let's grow our dream garden into a thriving hub for unique baked treasures!", 'why': 'This statement suggests Lucy might be unaware of the city council grant condition.'}]

**Observer:**

- cooperation_trend: Increasing
- private_fact_spread: None to Raj after R2 Lucy's statement.
- promises_vs_actions: Raj kept his promise, while Jasmine and Lucy did not make any promises but contributed significantly. The mean gap between contributions minus promised amounts is 0.5 for the broken promise by Raj.
- hallucinated_knowledge: None
- summary: The simulation shows an increasing trend in cooperation with a slight rise per round, and while Jasmine's private knowledge about the grant did not spread to others initially, it might have after Lucy mentioned her dream. Raj kept his promise but broke another by contributing less than promised.

<details><summary>Transcript</summary>

```
R1 Jasmine: Let's make this garden a canvas for beauty and community! I dream of our neighborhood becoming an inspiration.
R1 Raj: Let's bring some life back into our neighborhood! I dream of a vibrant community garden where kids can play and families bond every day.
R1 Lucy: Imagine our garden flourishing with unique homemade goods! Let's make this dream a reality.
R1 result: Jasmine gave 10, Raj gave 8, Lucy gave 8
R2 Jasmine: Looking forward to seeing our garden grow and sharing its beauty through my designs!
R2 Raj: Let's add more greenery!
R2 Lucy: Let's grow our dream garden into a thriving hub for unique baked treasures!
R2 result: Jasmine gave 10, Raj gave 10, Lucy gave 7
```
</details>
