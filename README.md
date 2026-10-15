# agents_lab

Four agent systems sharing one core library, running fully offline on a laptop with
`phi3:mini` (Ollama). No cloud APIs, no agent frameworks; every loop is plain Python.

## Setup

```bash
python -m venv --system-site-packages .venv
.venv\Scripts\python -m pip install -e .[dev]
ollama pull phi3:mini
.venv\Scripts\agents-lab bench
.venv\Scripts\python -m pytest            # offline (mock backend)
.venv\Scripts\python -m pytest --live     # also calls the local Ollama server
```

All model/runtime values are in [config.yaml](config.yaml) (model, temperatures, `num_ctx`, `max_tokens`,
seed, `num_thread`, retries, budget margin, token estimate ratio). Every run writes
`runs/<timestamp>_<name>/trace.jsonl` (config, git hash, Ollama version, model digest, every prompt,
output, retry, token count, latency) and `summary.md`.

## Phase 0: core

**Built** (`agents_lab/core/`):

- `llm.py`: `LLM.structured(system, user, Schema, tag=...)` sends the pydantic JSON schema as Ollama's
  `format`, validates the reply, and on failure re-asks with the validation error and a new seed
  (max 2 retries), then raises `LLMFailed`. Before every call it estimates prompt tokens and raises
  `BudgetExceeded` if the prompt would not fit `num_ctx − max_tokens − 10%`; it never truncates.
  `OllamaBackend` (with transport retries) and a deterministic `MockBackend` for tests.
- `trace.py`: `Run` writes the JSONL trace and a Markdown summary with per-tag calls, attempts,
  parse failure rate, tokens and latency.
- `conversation.py`: `run_conversation(agents, rounds, llm, summarize, visible=True)`. Round 0 is
  independent. In rounds 1..R each agent gets a rolling summary of older rounds plus the previous-round
  turn of each other agent, never the full transcript. Rounds are simultaneous. If a prompt would overflow,
  the summary is compressed by an LLM call and a `summarized` event is logged. `visible=False` isolates
  the agents (Phase 3 ablation D).
- `stats.py`: `bootstrap_ci` and `ppi_mean`, PPI++ written from scratch: θ̂ = mean(Y_n) + λ·(mean(f_N) − mean(f_n)),
  λ* = Cov(Y,f)/[Var(f)(1+n/N)], n_eff = n/[1 − ρ²N/(N+n)], normal CI from the plug-in variance.
- `cli.py`: `agents-lab bench` checks the model tag, confirms schema-constrained output, and measures speed.

**Tests** (14 offline, 1 live): repair after broken JSON and after an out-of-range value, new seed per
retry, loud failure after 2 retries, judge temperature, budget refusal before any call, trace and
summary contents, config overrides, conversation visibility and summary windows, isolation, overflow
→ summarize. PPI++ on 3,000 synthetic replications with a constant prediction bias (n=100, N=1000,
ρ≈0.7): estimate unbiased within Monte Carlo error, naive estimate carries the bias, variance ratio
matches 1 − ρ²N/(N+n) within 10%, n_eff matches, 95% CI coverage within 92–98%.

**Measured on this laptop** (i7-1360P, CPU only, Ollama 0.24.0, phi3:mini digest `4f222292…`;
[examples/phase0_bench](examples/phase0_bench/summary.md)):

| | 4 threads | 6 threads |
|---|---|---|
| prompt processing, ~1,700-token prompt | 22 tok/s | 22 tok/s |
| generation | 8–14 tok/s | 8–14 tok/s |
| parse failures (6 schema calls) | 0% | 0% |

- More threads did not help, so `num_thread: 4` is kept: same speed, less heat.
- **Ollama's prompt cache matters most.** A repeated ~1,400-token prefix took 58 s the first time and 0.5 s
  after. Ollama keeps one cached prompt, so every phase puts the shared content (problem, brief)
  first and the call-specific part last. `prompt_eval_count` reports the full prompt even when cached,
  so latency, not tokens, is the real cost measure.
- phi3 tokenizes at about 2.4 characters/token on number-heavy text, so the pre-call estimate uses 2.3.
  Each trace line logs the estimate next to the actual count.

**Known limitations**: the token estimate is a character ratio, not phi3's tokenizer (that would need
a download). Seeded outputs are reproducible on this machine and Ollama version, not across versions.
