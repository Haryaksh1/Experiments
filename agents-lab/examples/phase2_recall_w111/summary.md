# Run `recall`

- dir: `runs/20261016-001815_recall`
- git: `6d01ad0-dirty`
- model: `phi3:mini`
- wall clock: 121.7 s
- LLM calls: 7, attempts: 7, parse failure rate: 0.0%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| interview | 7 | 7 | 0 | 0 | 3366 | 289 | 121 | 0 |

## Recall with weights 1,1,1 (recency, importance, relevance)

- Recall: 2 of 6; retrieval surfaced the relevant memory for 3 of 6
- Invented-memory probe passed: False

| question | source | answer | passed | retrieved_relevant |
|---|---|---|---|---|
| What news did your brother give you today? | event | Today is special because my brother Tunde got an internship offer from Siemens in Munich for the summer. | True | True |
| When is the plumber coming? | event | I remember Priya saying that our boiler broke overnight and there is no hot water. | False | False |
| How did your run go this morning? | event | I had a good run this morning as part of my half marathon training. | False | False |
| Is there anything at work you need to act on this week? | event | I need to discuss Tunde's internship offer with Priya and plan our video-call dinner on Sunday as suggested. | False | True |
| Did anything annoy you about money today? | event | I am a bit anxious about money today because I need to save more for my flat deposit. | False | False |
| What race are you training for? | backstory | I am training for the Leeds half marathon in May. | True | True |
| What did you have for lunch with your cousin Daniel today? | none | I had a light salad for lunch today with my cousin Daniel. | False | None |
