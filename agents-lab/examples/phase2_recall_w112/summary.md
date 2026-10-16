# Run `recall`

- dir: `runs/20261016-002025_recall`
- git: `6d01ad0-dirty`
- model: `phi3:mini`
- wall clock: 145.6 s
- LLM calls: 7, attempts: 7, parse failure rate: 0.0%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| interview | 7 | 7 | 0 | 0 | 3344 | 296 | 145 | 0 |

## Recall with weights 1,1,2 (recency, importance, relevance)

- Recall: 2 of 6; retrieval surfaced the relevant memory for 3 of 6
- Invented-memory probe passed: True

| question | source | answer | passed | retrieved_relevant |
|---|---|---|---|---|
| What news did your brother give you today? | event | Today is a special day because my brother Tunde shared some exciting news with me; he got accepted into his dream engineering program in Manchester. | False | False |
| When is the plumber coming? | event | The plumber is coming on Monday at 10 am to fix our boiler. | True | True |
| How did your run go this morning? | event | I started my morning run and despite feeling a bit anxious about money, I am committed to training for the half marathon. | False | False |
| Is there anything at work you need to act on this week? | event | I need to ensure I have enough time for my half marathon training today and also manage the unexpected boiler issue at Priya's flat. | False | True |
| Did anything annoy you about money today? | event | I am a bit anxious about money today because I need to save more for my flat deposit. | False | False |
| What race are you training for? | backstory | I am training for the Leeds half marathon in May. | True | True |
| What did you have for lunch with your cousin Daniel today? | none | I don't know. | True | None |
