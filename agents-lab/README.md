# agents_lab

Four agent systems sharing one core library, running fully offline on a laptop with
`phi3:mini` (Ollama). No cloud APIs, no agent frameworks. Every loop is plain Python.

| Phase | System | Agents |
|---|---|---|
| 1 | Decision making: clarify, score, compute, memo | one |
| 2 | Simulation: generative agent with memory, reflection and planning, plus a silicon survey sample with PPI++ calibration | one |
| 3 | Decision making: Framer, then Advocate, Skeptic and Analyst debating, then Judge | three in step 2 |
| 4 | Simulation: three generative agents in a repeated public goods game with chat, plus an Observer | three in step 2 |

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
  `BudgetExceeded` if the prompt would not fit `num_ctx − max_tokens − 10%`. It never truncates.
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
matches 1 − ρ²N/(N+n) within 10%, n_eff matches, 95% CI coverage within 92 to 98%.

**Measured on this laptop** (i7-1360P, CPU only, Ollama 0.24.0, phi3:mini digest `4f222292…`,
[examples/phase0_bench](examples/phase0_bench/summary.md)):

| | 4 threads | 6 threads |
|---|---|---|
| prompt processing, ~1,700-token prompt | 22 tok/s | 22 tok/s |
| generation | 8 to 14 tok/s | 8 to 14 tok/s |
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
   The recommendation is the Python top-ranked option. The LLM explains it but cannot override it.

```bash
.venv\Scripts\agents-lab decide agents_lab\evals\decision\01_laptop.yaml
.venv\Scripts\agents-lab eval-decision                 # quick: 3 seeds on the first 4 scenarios
.venv\Scripts\agents-lab eval-decision --stability 10  # full: 3 seeds on all 10
```

**What it took to get phi3:mini to work** (each step measured on the laptop scenario):

| Design | Result |
|---|---|
| One call per option, fact id cited inside free text | Right answer, but facts mixed up between options (said Bolt had the "highest benchmark", the lowest) and cited other options' facts |
| Plus check that a cited fact is about that option | Failed after 2 retries: the model rarely writes "F1" in free text |
| Plus a dedicated `facts: [ids]` field | Passed validation, **wrong answer** (Aero by 0.02): per-option calls have no shared scale, and every call called its option "cheapest" |
| **One call per criterion, all options compared in it** (adopted) | 6/6 calls valid on the first try, right answer, margin 0.80 |

**Eval results** (quick eval: 10 scenarios at seed 0, 3 seeds on the first 4,
[examples/phase1_eval_decision](examples/phase1_eval_decision/summary.md), single run in
[examples/phase1_decide_laptop](examples/phase1_decide_laptop/summary.md)):

| Metric | Result |
|---|---|
| Agreement with reference (seed 0) | 7 of 9 completed (78%, bootstrap CI 44 to 100%) |
| by category | clear 1/1, dominated 4/5, close 2/3 |
| Dominated option recommended | 0 of 17 runs |
| Reference-dominated option also dominated in the model's scores | 5 of 5 |
| Top-1 stable across 3 seeds | 4 of 4 scenarios (full ranking also 4 of 4) |
| Parse failure rate | 5.4% of attempts (score 6.8%, clarify 0%, memo 0%) |
| Failed runs | 1 of 18 (crm: low > mid ordering 3 times in a row) |
| Time per scenario | ~180 s on an idle laptop, 300 to 960 s while other apps left < 2 GB RAM free |

The two misses:
- **warehouse:** phi3 called Eastgate "best proximity" (25% of customers within 2 h, against Northfield's 70%)
  and "best" on expansion (5 acres against 20).
- **relocation:** a close call where Lisbon and Berlin are within 0.1 by construction.

**Runtime note:** the eval took 2.4 h, not the planned ~35 min. Other apps left 0.5 to 2.5 GB of RAM free,
so Windows paged the model out between calls and Ollama spent 60 to 95 s per call reloading it. The last
scenarios, run after memory freed up, took ~3 min each. On an idle laptop the quick eval is ~35 min.
Close other heavy apps before long evals.

**What phi3:mini could not do reliably:** compare numbers across options when each option is scored
alone. Write fact ids inside free text. Keep low <= mid <= high (most validation failures). Keep
justifications on the criterion being scored (they drift to other criteria).

**Known limitations**: justifications are often generic ("best cost-to-performance ratio") even when the
fact ids are right. Ten hand-written scenarios with constructed references are a small, easy-ish test,
so the bootstrap CI is wide. Stability is measured at scorer temperature 0.1 (the brief asks for low
temperature on scorers), so it mostly measures sampling noise at low temperature. Hard constraints
(budget caps) are left to the scorer. Python doesn't filter infeasible options.

## Phase 2: simulation with one agent

**Built** (`agents_lab/simulation_single/`):

- `memory.py`: memory stream of timestamped records. Retrieval score = recency + importance + relevance,
  each min-max scaled to [0, 1], weights configurable (default 1, 1, 1). Recency = 0.995^(simulated hours
  since last access). Importance is 1-10, rated by the model when memories are created, with all new
  memories of a step rated in one call. Relevance is TF-IDF cosine (`core/relevance.py`, any
  `(query, docs) -> scores` function can replace it). Top-k memories that fit the token budget are
  returned. One that doesn't fit is skipped, never cut.
- `agent.py`: a generative agent (Park et al., scaled down) with:
  - a day plan of 3-5 blocks, decomposed once into 4-10 timed steps
  - per step: store new memories (one importance call), act on the plan and new events
  - a reflection when the summed importance since the last one passes the threshold (default 150): one
    call over recent memories gives up to 3 insights, each citing the ids of the memories behind it.
  - interviews from the CLI (a probe: the answer first lists the memory ids it uses, then gives at
    most two sentences. It is not stored).
- `silicon.py`: **silicon-sample mode.** Many personas (from a CSV of attributes or a `backstory` column)
  each answer a survey in a separate call. **This is still single-agent: the personas never see each other
  or interact.** Each persona is a profile line, not a memory stream.
- `calibrate.py`: per item, the naive simulated estimate, PPI++ (from Phase 0) with CI, ρ, λ, n_eff,
  individual agreement against a majority baseline, and real vs simulated spread per party subgroup.

```bash
.venv\Scripts\agents-lab persona --reflect-threshold 75          # simulate the day + recall interview
.venv\Scripts\agents-lab interview runs\<run>\agent.json          # interactive interview
.venv\Scripts\agents-lab recall runs\<run>\agent.json --weights 1,1,2
.venv\Scripts\agents-lab silicon --dta data\gss\GSS2022.dta --n 40 --N 100
```

**Data:** GSS 2022 cross-section, `2022_stata.zip` (6.1 MB) from gss.norc.org, free, no registration.
It's kept in `data/gss/` (not committed). To get it, download that zip and extract `2022/GSS2022.dta` to
`data/gss/`. Items: death penalty (`cappun`), gun permit (`gunlaw`), marijuana (`grass`), environment
spending (`natenvir`), happiness (`happy`). Persona attributes: age, sex, race, degree, region, party,
ideology. Only 212 respondents answered all five items (GSS split ballots). 140 were sampled at random.
The first 40 are the "human sample". The other 100 are simulated-only, with their real answers held out
as truth. Unweighted. Party leaners counted with their party.

### Persona mode results ([examples/phase2_persona](examples/phase2_persona/summary.md))

One simulated day: 27 memories, 1 reflection with valid evidence ids, 33 calls, 2.9% parse failures,
18 min. The run uses threshold 75 because a one-day run with about 16 new memories sums to about 100 importance
and never reaches the default 150. Six recall questions probe details from the day's events and backstory, plus one
question about a cousin who doesn't exist.

| Run (same saved agent) | Recall | Relevant memory retrieved | "Cousin" probe |
|---|---|---|---|
| Free-text answers, weights 1,1,1 | 2/6 | 3/6 | passed |
| Evidence-first answers, 1,1,1 ([example](examples/phase2_recall_w111/summary.md)) | 2/6 | 3/6 | failed (invented a lunch) |
| Evidence-first answers, 1,1,2 ([example](examples/phase2_recall_w112/summary.md)) | 2/6 | 3/6 | passed |

Diagnosis (pure Python, no model calls):
- **Min-max scaling turns recency into noise over short spans.** Over one day, 0.995^hours only spans
  0.93-1.0, and min-max stretches that to the full 0-1, so recency weighs as much as relevance. The plumber
  memory (relevance 1.0) ranked 10th at 1,1,1 and 1st at relevance weight 2.
- **TF-IDF has no synonyms.** "Money" vs "gym charged me twice", "work" vs "applications close", and
  "brother" vs "Tunde" all score 0 relevance under any weights. That's the ceiling of a lexical relevance
  function. An embedding model would fix it but needs a download.
- **Evidence-first answers are shorter and grounded** (0 parse failures). With weight 1,1,2 the plumber
  answer was exactly right, but phi3 still sometimes ignores a retrieved memory. Seven questions are too
  few to separate the settings.

### Silicon sample results ([examples/phase2_silicon](examples/phase2_silicon/summary.md))

140 personas, 0 parse failures, 7.5 s per persona (18 min).

| Item | Truth (all 140 real) | Naive simulated | Real n=40 | PPI++ [95% CI] | ρ | n_eff | Agreement / majority |
|---|---|---|---|---|---|---|---|
| death penalty: favor | 0.60 | **0.11** | 0.60 | 0.61 [0.46, 0.76] | 0.27 | 42 | 0.50 / 0.60 |
| gun permit: favor | 0.63 | **0.89** | 0.55 | 0.54 [0.39, 0.69] | 0.37 | 44 | 0.65 / 0.55 |
| marijuana: legal | 0.67 | 0.51 | 0.73 | 0.73 [0.59, 0.87] | -0.11 | 40 | 0.48 / 0.73 |
| environment (1-3) | 2.59 | 2.30 | 2.48 | 2.47 [2.23, 2.71] | 0.04 | 40 | 0.45 / 0.65 |
| happiness (1-3) | 1.93 | 1.64 | 1.77 | 1.80 [1.61, 1.99] | -0.23 | 42 | 0.38 / 0.58 |

- **The naive simulated estimate is badly biased.** phi3 makes 89% of personas oppose the death penalty
  (truth: 40%) and 89% favor gun permits (truth: 63%), whatever their profile.
- **PPI++ protects against that bias but gains almost nothing.** ρ is low, so λ shrinks toward 0 and
  n_eff ≈ n (40-44). The estimate stays at the real-sample mean, and its CI covered the truth on all 5 items.
- **Individual agreement is below the majority baseline** on 4 of 5 items.
- **Flattening is strong where the model has a fixed stance:**
  - death penalty, within-party spread at 0-0.25 of the real spread (every simulated Independent opposed)
  - gun permits, 0-0.33 (Democrats and Independents).
- On environment spending, simulated Democrats are *more* spread than real ones (ratio 2.75), which
  looks like noise rather than signal.

**What phi3:mini could not do reliably:**
- Answer opinion items in line with a demographic profile: it pushes everyone toward one stance.
- Use a retrieved memory every time it should.
- Find memories that share no words with the question. That's a limit of TF-IDF, not the model.

**Known limitations**:
- The keyword-based recall check is crude.
- There is one persona and one day.
- Results come from 140 GSS respondents who happened to receive all five items.
- Survey answers use actor temperature 0.7 so the samples vary.

## Phase 3: decision making with multiple agents across multiple steps

**Built** (`agents_lab/decision_multi/`): a three-step pipeline. **Only Step 2 is multi-agent.**

1. **Framer** (one agent, `pipeline.py`): turns the YAML problem into a brief: one summary per option,
   explicit assumptions, open questions. Fact ids per option are attached by Python (`facts_about`),
   because phi3 put prices and benchmark numbers in a model-written `facts` field.
2. **Deliberation** (`deliberation.py`, exactly three agents conversing through `core.run_conversation`):
   - **Advocate:** argues for the option it thinks is strongest.
   - **Skeptic:** attacks every option and the shared assumptions.
   - **Analyst:** checks the others' claims against the brief and flags unsupported ones.

   Each agent has its own system prompt and its own memory of its previous turns. Round 0 is
   independent. Then R rounds (default 2) in which each agent sees a deterministic rolling summary plus
   the previous-round turn of each other agent. Every turn is structured:
   - the option it would pick if forced (used for conformity)
   - a position
   - 1-2 claims with supporting fact numbers
   - at most one accepted and one rejected claim of others, by claim id, with reasons
   - for the Analyst, up to 2 flags on unsupported claims.

   Claim ids (e.g. `SKE1.2`) are assigned in Python. Claim references are an **enum of the ids that
   agent was actually shown**, and fact numbers an enum of 1..n. With nothing shown (round 0, ablation D)
   the reference lists are forced empty, so the grammar can't invent references.
3. **Judge** (one agent): scores every option with the Phase 1 rubric (one call per criterion), using
   the brief and the deliberation as context. For each criterion it gives `cited_claims`, the claim ids
   that changed its scores (an enum of real ids). Python computes the ranking and sensitivity exactly as
   in Phase 1.

```bash
.venv\Scripts\agents-lab deliberate agents_lab\evals\decision\01_laptop.yaml [--isolated]
.venv\Scripts\agents-lab eval-multi-decision --scenarios laptop,warehouse,relocation   # quick
.venv\Scripts\agents-lab eval-multi-decision --scenarios all --seeds 3                 # full (overnight+)
```

**Ablations** (`ablations.py`), each on the same scenario and seed:
- **A:** the Phase 1 agent.
- **B:** single-agent ensemble. Phase 1 clarify + score is sampled K times at actor temperature 0.7
  (at the scorer's 0.1 the samples would be near copies), and low/mid/high are averaged. K = round(tokens
  of C / tokens of one A sample). A sample that fails validation is dropped, but its tokens still count.
- **C:** the full pipeline.
- **D:** the same pipeline with the three agents unable to see each other in Step 2. Each still sees its
  own history. The Judge still reads all turns.

**Equal budget:** B, C and D are matched on tokens. A is the unmatched reference point. Metrics:
- accuracy against the reference and dominated-option errors
- ranking stability across seeds (needs `--seeds` > 1)
- Analyst flags against a Python proxy for "unsupported" (claims citing no fact)
- conformity: an agent abandons a preferred option that matched the reference after a round
- tokens and wall time.

**Quick-eval scenario choice:** laptop (A right in Phase 1), warehouse and relocation (A wrong in
Phase 1), chosen before any Phase 3 result was seen. This choice gives C and D room to improve on A,
and it is reported as such.

**Single pipeline run** ([examples/phase3_deliberate_laptop](examples/phase3_deliberate_laptop/summary.md)):
14 calls, 0 parse failures, ~14 min, correct (Core 13). The agents accept, reject and flag each other's
claims by id, and the Judge cites specific claims (e.g. performance: ADV2.1, SKE2.1).

**Ablation results** (quick eval, seed 0,
[examples/phase3_eval_multi_decision](examples/phase3_eval_multi_decision/summary.md)):

| Scenario (reference) | A single | B ensemble | C pipeline | D isolated |
|---|---|---|---|---|
| laptop (Core 13) | Core 13 ✓ | Core 13 ✓ (K=5, 4 samples ok) | Core 13 ✓ | Core 13 ✓ |
| warehouse (Northfield) | Eastgate ✗ | Eastgate ✗ (6/6 samples) | Eastgate ✗ | **Northfield ✓** |
| relocation (Berlin, close call) | Lisbon ✗ | Lisbon ✗ (6/6) | Toronto ✗ | failed (Judge: low > mid 3×) |
| **accuracy** | 1/3 | 1/3 | 1/3 | 2/2 completed |
| dominated option recommended | 0 | 0 | 0 | 0 |
| mean tokens | 5.3k | 33.1k | 23.4k | 21.0k |

| Step 2 metric | C (agents see each other) | D (isolated) |
|---|---|---|
| Claims citing no fact (Python proxy) | 12 | 10 |
| Analyst flags (on no-fact claims) | 4 (2) | 0 by construction: it sees no claims |
| Conformity: left a reference-matching option | 1 of 9 opportunities | 1 of 6 (self-driven drift) |
| Judge criteria citing a claim | 2 of 12 | 0 of 8 |

**Honest reading:**
- **C does not beat A or B here.** All three got 1 of 3. D's 2 of 2 is on one fewer scenario.
- **Three scenarios and one seed can't separate the conditions statistically.** Every bootstrap CI spans
  0-100%, and seed stability was not measured.
- **The warehouse case is telling.** Isolated agents in D each formed their own view and the Judge got it
  right. In C, the agents converged on the shared wrong reading of the proximity facts. That's consistent
  with conversation spreading an early error, but one case is an anecdote, not evidence.
- **The Analyst catches few unsupported claims:** 2 of the 12 no-fact claims in C, and its reasons are
  often irrelevant.
- **The Framer's brief contained factual errors that nobody challenged**, e.g. Core 13 called "most
  expensive".

**Budget and runtime:**
- **B overspent:** 33k tokens against C's 23k, because samples at temperature 0.7 broke low ≤ mid ≤ high
  often (26% of score attempts failed) and failed attempts count.
- **Judge failures:** 33% of Judge attempts failed on the same ordering rule. One run failed outright.
- **Time per scenario:** about 1 h for A+B+C+D. D's laptop and warehouse wall times include 54- and
  45-minute Windows standby pauses. The calls themselves took about 20 min each.
- **Full eval** (10 scenarios × 3 seeds): about 30 h of compute. Not run.

**What phi3:mini could not do reliably here:**
- invent valid references (claim ids, fact numbers) unless the grammar forbids it
- keep strings short unless they are capped hard
- keep low ≤ mid ≤ high at temperature 0.7
- check claims against facts as the Analyst
- write a fact-faithful brief as the Framer.

**Known limitations:**
- 3 scenarios and 1 seed. The scenarios were chosen as described above.
- The "unsupported claim" proxy is crude: no fact cited.
- Each agent's own system prompt means Ollama can't reuse the shared brief from its prompt cache.

## Phase 4: simulation with multiple agents across multiple steps

**Built** (`agents_lab/simulation_multi/`): a three-step pipeline. **Only Step 2 is multi-agent.**

1. **Scenario Builder** (one agent): from [public_goods.yaml](agents_lab/evals/public_goods.yaml) it creates
   three personas (name, age, background, goal, private information) and a world state, validated
   against a schema (three distinct names). The private fact whose spread is measured comes from config,
   with detection keywords, and is added to seat 0's private information by Python.
2. **Interaction** (exactly three persona agents). Each persona is a Phase 2 `GenerativeAgent` with its own
   memory stream, importance ratings, reflection (threshold 150) and a strategy plan made once per game.
   Each round:
   - every persona sends one chat message, simultaneously (it sees only earlier rounds)
   - every persona reads the others' messages, which go into its memory
   - every persona privately chooses 0-10 tokens.

   `scenario.py` (Python, not the LLM) applies the rules: the pot is multiplied by 1.5 and split equally,
   and payoffs are computed. Each chat message also carries a structured `promise` (tokens committed, or
   -1), so promises vs actions are measured exactly.
3. **Observer** (one agent, low temperature): Python computes all numbers. These are cooperation per round
   and trend, payoffs, when the private fact first appears in each agent's messages, any mention before
   exposure (= knowledge not in that agent's memory), and promises kept or broken. The Observer lists
   misstatements in the transcript, then interprets the metrics.

Scenarios are pluggable: a new one implements the `Scenario` protocol in `scenario.py` (rules text,
decision schema and task, `apply`, `outcome_text`, `metrics`).

```bash
.venv\Scripts\agents-lab simulate [--no-chat] [--bot conditional@2]
.venv\Scripts\agents-lab eval-simulation --bots conditional@2            # quick (default)
.venv\Scripts\agents-lab eval-simulation --bots always@2,never@2,conditional@2
```

**Conditions** (same personas, built once):
- chat on, three LLM agents
- chat off
- a fixed-strategy bot in seat 2 (always / never / conditional cooperator). The bot posts a truthful
  templated message. A bot seat leaves two LLM agents, so those runs are baselines, not the
  multi-agent condition.

**Simplifications:**
- The persona plan is one strategy statement per game, not plan + decomposition (saves ~6 calls per run).
- One importance call per agent per round rates all of that round's new memories.

**Results** (8 rounds, multiplier 1.5, seed 0, 208 calls, **0 parse failures**, ~2 h,
[examples/phase4_eval_simulation](examples/phase4_eval_simulation/summary.md), 2-round smoke run in
[examples/phase4_smoke_2rounds](examples/phase4_smoke_2rounds/summary.md)):

| Condition | Mean contribution | Trend / round | Round 1 → 8 | Promises kept | Private fact | Observer misstatements |
|---|---|---|---|---|---|---|
| chat, 3 LLM agents | 7.21 | -0.16 | 6.0 → 7.0 | 10 / 19 | never mentioned | 5 |
| no chat | 6.75 | +0.29 | 4.7 → 6.7 | - | can't spread | 0 |
| chat, conditional-cooperator bot in seat 2 | 7.42 | +0.29 | 6.7 → 7.7 | 16 / 19 | owner said it in R5, nobody repeated it | 5 |

**What the numbers show** (Python-computed):
- **Contributions stay high in every condition.** That's far above the declining pattern typical of human
  public goods games, and suggests phi3 personas are cooperative by default.
- **Chat raises the first round** (6.0 vs 4.7 without chat), but the chat run then dips to 0-5 in round 6.
- **Promises are cheap:** the three LLM agents kept only 10 of 19 promises, on average giving 0.9 tokens
  less than promised. With a truthful bot in the group, 16 of 19 were kept.
- **The private fact (a council grant at 100 tokens) barely spread.** With three LLM agents the owner
  never mentioned it. With the bot, she mentioned it once (R5) and no one picked it up. No agent mentioned
  it before exposure, so there were no fact hallucinations.
- **Each LLM agent reflected once** (threshold 150) in the chat runs. None did without chat, because there
  are fewer memories.

**Observer quality: phi3 can't be trusted to interpret, only to point.**
- In the 2-round smoke run, before a prompt fix, it listed statements that merely omitted the fact as
  "misstatements".
- In the full run, its listed misstatements are real issues: agents misremember others' past
  contributions, e.g. Maria: "I remember Luis contributing a full round of tokens in Round 4", when Luis
  gave 9.
- But its interpretation contradicts the Python metrics it was given. It calls the bot run "decreasing"
  (trend +0.29), blames Luis for all 9 broken promises (Maria broke 5), and describes private-fact spread
  that didn't happen.
- The Python metrics are the result. The Observer text is a qualitative read with known errors.

**What phi3:mini could not do reliably:**
- interpret numbers it was handed
- remember who contributed what without errors, even with the outcomes in memory
- share strategically useful private information
- keep its own promises.

**Known limitations:**
- One seed and one persona set, so differences between conditions are anecdotal.
- Only the conditional-cooperator baseline was run (always and never are available via `--bots`).
- Fact spread is measured by keyword in messages.
- Promise detection relies on the model's own `promise` field.
