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

## Phase 1: decision making with one agent

**Built** (`agents_lab/decision_single/`): a YAML problem (question, options, weighted criteria with a
direction, numbered facts, uncertainties, constraints, plus an eval-only `reference`) goes through one agent
with its own system prompt and memory:

1. **Clarify** (1 call): missing information and explicit assumptions.
2. **Score** (1 call per criterion, scorer temperature 0.1): every option gets low/mid/high 0-10, the ids of
   the facts used, a one-line justification, and `basis: fact | assumption`. Validation rejects
   low > mid > high orderings and fact ids that aren't about that option (`Problem.facts_about`), and
   re-asks with the exact error.
3. **Compute in Python** (`compute.py`): PERT expected score per cell `(low + 4·mid + high)/6`, weighted
   EV per option with all-low/all-high range, dominance on expected scores, and closed-form sensitivity: the
   smallest single weight change (others renormalized) and the smallest single score change that flips
   the top choice, and to whom.
4. **Memo** (1 call): rationale, confidence, key risks, evidence that would change the decision.
   The recommendation is the Python top-ranked option; the LLM explains it but cannot override it.

```bash
.venv\Scripts\agents-lab decide agents_lab\evals\decision\01_laptop.yaml
.venv\Scripts\agents-lab eval-decision                 # quick: 3 seeds on the first 4 scenarios
.venv\Scripts\agents-lab eval-decision --stability 10  # full: 3 seeds on all 10
```

**What we learned getting phi3:mini to work** (each step measured on the laptop scenario):

| Design | Result |
|---|---|
| One call per option, fact id cited inside free text | Right answer, but facts mixed up between options (said Bolt had the "highest benchmark", the lowest) and cited other options' facts |
| Plus check that a cited fact is about that option | Failed after 2 retries: the model rarely writes "F1" in free text |
| Plus a dedicated `facts: [ids]` field | Passed validation, **wrong answer** (Aero by 0.02): per-option calls have no shared scale, and every call called its option "cheapest" |
| **One call per criterion, all options compared in it** (adopted) | 6/6 calls valid on the first try, right answer, margin 0.80 |

**Eval results** (quick eval: 10 scenarios at seed 0, 3 seeds on the first 4;
[examples/phase1_eval_decision](examples/phase1_eval_decision/summary.md), single run in
[examples/phase1_decide_laptop](examples/phase1_decide_laptop/summary.md)):

| Metric | Result |
|---|---|
| Agreement with reference (seed 0) | 7 of 9 completed (78%, bootstrap CI 44–100%) |
| by category | clear 1/1, dominated 4/5, close 2/3 |
| Dominated option recommended | 0 of 17 runs |
| Reference-dominated option also dominated in the model's scores | 5 of 5 |
| Top-1 stable across 3 seeds | 4 of 4 scenarios (full ranking also 4 of 4) |
| Parse failure rate | 5.4% of attempts (score 6.8%, clarify 0%, memo 0%) |
| Failed runs | 1 of 18 (crm: low > mid ordering 3 times in a row) |
| Time per scenario | ~180 s on an idle laptop; 300–960 s while other apps left < 2 GB RAM free |

The two misses:
- **warehouse:** phi3 called Eastgate "best proximity" (25% of customers within 2 h, against Northfield's 70%)
  and "best" on expansion (5 acres against 20).
- **relocation:** a close call where Lisbon and Berlin are within 0.1 by construction.

**Runtime note:** the eval took 2.4 h, not the planned ~35 min. Other apps left 0.5–2.5 GB of RAM free,
so Windows paged the model out between calls and Ollama spent 60–95 s per call reloading it. The last
scenarios, run after memory freed up, took ~3 min each. On an idle laptop the quick eval is ~35 min.
Close other heavy apps before long evals.

**What phi3:mini could not do reliably:** compare numbers across options when each option is scored
alone. Write fact ids inside free text. Keep low <= mid <= high (most validation failures). Keep
justifications on the criterion being scored (they drift to other criteria).

**Known limitations**: justifications are often generic ("best cost-to-performance ratio") even when the
fact ids are right. Ten hand-written scenarios with constructed references are a small, easy-ish test,
so the bootstrap CI is wide. Stability is measured at scorer temperature 0.1 (the brief asks for low
temperature on scorers), so it mostly measures sampling noise at low temperature. Hard constraints
(budget caps) are left to the scorer; Python doesn't filter infeasible options.
