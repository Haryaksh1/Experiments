# Run `bench`

- dir: `runs/20261015-201235_bench`
- git: `no-commit`
- model: `phi3:mini`
- wall clock: 315.3 s
- LLM calls: 6, attempts: 6, parse failure rate: 0.0%

## LLM calls by tag

| tag | calls | attempts | failed_attempts | final_failures | prompt_tokens | completion_tokens | latency_s | parse_fail_rate |
|---|---|---|---|---|---|---|---|---|
| bench_long | 3 | 3 | 0 | 0 | 5215 | 341 | 278 | 0 |
| bench_short | 3 | 3 | 0 | 0 | 171 | 414 | 35.8 | 0 |

Ollama 0.24.0, digest `4f222292793889a9a40a020799cfd28d53f3e01af25d48e06c5e708610fc47e9`, num_thread=4

## Means per prompt size

| tag | prompt_tokens | completion_tokens | prompt_tok_s | gen_tok_s | latency_s | chars_per_token |
|---|---|---|---|---|---|---|
| bench_long | 1.74e+03 | 114 | 22.4 | 7.86 | 92.8 | 2.56 |
| bench_short | 57 | 138 | 53.8 | 13.8 | 11.9 | 2.35 |
