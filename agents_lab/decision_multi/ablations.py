"""Phase 3 ablations on the Phase 1 scenarios.

A: Phase 1 single agent.
B: single-agent ensemble: Phase 1 (clarify + score) sampled K times at actor temperature, low/mid/high
   averaged; K = round(tokens of C / tokens of one A sample), so B and C spend about the same tokens.
C: full Phase 3 pipeline.
D: Phase 3 with the three agents unable to see each other in Step 2.
"""
import time

import pandas as pd

from agents_lab.core.conversation import Turn
from agents_lab.core.llm import LLM, LLMFailed
from agents_lab.core.stats import bootstrap_ci
from agents_lab.core.trace import md_table
from agents_lab.decision_single.agent import DecisionAgent
from agents_lab.decision_single.compute import analyze_lmh, matrices
from agents_lab.decision_single.schemas import Problem
from agents_lab.decision_multi.deliberation import CLAIM_ID
from agents_lab.decision_multi.pipeline import run_pipeline


def spent(llm: LLM, start: int, tags: set[str] | None = None) -> int:
    """Tokens (prompt + completion) of LLM attempts logged since event index `start`."""
    return sum(e["prompt_tokens"] + e["completion_tokens"] for e in llm.run.events[start:]
               if e["event"] == "llm_call" and (tags is None or e["tag"] in tags))


def run_ensemble(p: Problem, llm: LLM, k: int, seed: int):
    """K samples; a sample that fails validation after its retries is dropped (its tokens still count)."""
    samples = []
    for i in range(k):
        try:
            samples.append(DecisionAgent(llm, seed=seed + 1000 * (i + 1), low_temperature_scoring=False)
                           .run(p, memo=False))
        except LLMFailed:
            llm.run.log("ensemble_sample_failed", problem_id=p.id, sample=i)
    if not samples:
        raise LLMFailed(f"{p.id}: all {k} ensemble samples failed")
    mats = [matrices(r.cells) for r in samples]
    avg = [sum(m[j] for m in mats) / len(samples) for j in range(3)]
    return analyze_lmh(*avg, p.weights), [r.recommendation for r in samples]


def conformity(turns: list[Turn], reference: str) -> tuple[int, int]:
    """(abandon events, opportunities): an agent whose preferred option matched the reference in
    round r-1 and no longer does in round r, after (in C) seeing the others."""
    by_agent: dict[str, list[str]] = {}
    for t in sorted(turns, key=lambda t: t.round):
        by_agent.setdefault(t.agent, []).append(t.content.preferred_option)
    events = opps = 0
    for prefs in by_agent.values():
        for prev, cur in zip(prefs, prefs[1:]):
            if prev == reference:
                opps += 1
                events += cur != reference
    return events, opps


def claim_stats(turns: list[Turn]) -> dict:
    """Analyst flags vs a Python proxy for 'unsupported': claims citing no fact."""
    from agents_lab.decision_multi.deliberation import claim_ids

    no_fact = {cid for t in turns for cid, c in zip(claim_ids(t.agent, t.round, t.content), t.content.claims)
               if not c.facts and t.agent != "Analyst"}
    flagged = {r.claim for t in turns if t.agent == "Analyst" for r in getattr(t.content, "flags", [])}
    total = sum(len(t.content.claims) for t in turns if t.agent != "Analyst")
    return {"claims_by_others": total, "no_fact_claims": len(no_fact), "analyst_flags": len(flagged),
            "flags_on_no_fact": len(flagged & no_fact)}


def evaluate(problems: list[Problem], llm: LLM, rounds: int = 2, n_seeds: int = 1) -> pd.DataFrame:
    rows = []
    for p in problems:
        ref = p.reference
        for s in [llm.cfg.seed + k for k in range(n_seeds)]:
            base = dict(scenario=p.id, category=ref.category, seed=s, reference=ref.best)

            def record(cond, rec, start, t0, **extra):
                rows.append({**base, "condition": cond, "recommendation": rec, "correct": rec == ref.best,
                             "dominated_recommended": rec in ref.dominated, "tokens": spent(llm, start),
                             "seconds": round(time.perf_counter() - t0, 1), "error": None, **extra})
                llm.run.log("ablation_row", **rows[-1])

            def attempt(cond, fn):
                start, t0 = len(llm.run.events), time.perf_counter()
                try:
                    return fn(start, t0)
                except LLMFailed as e:
                    rows.append({**base, "condition": cond, "error": str(e), "tokens": spent(llm, start),
                                 "seconds": round(time.perf_counter() - t0, 1)})
                    return None

            def cond_a(start, t0):
                r = DecisionAgent(llm, seed=s).run(p)
                record("A", r.recommendation, start, t0)
                return spent(llm, start, {"clarify", "score"})

            def cond_cd(visible):
                def f(start, t0):
                    r = run_pipeline(p, llm, rounds=rounds, visible=visible, seed=s)
                    ev, op = conformity(r.turns, ref.best)
                    cited = sum(bool(v) for v in r.cited.values())
                    record("C" if visible else "D", r.recommendation, start, t0, conformity_events=ev,
                           conformity_opps=op, judge_criteria_citing=cited, **claim_stats(r.turns))
                    (llm.run.dir / "results").mkdir(exist_ok=True)
                    (llm.run.dir / "results" / f"{p.id}_seed{s}_{'C' if visible else 'D'}.md").write_text(
                        r.to_markdown(), encoding="utf-8")
                    return spent(llm, start)
                return f

            sample_tokens = attempt("A", cond_a)
            c_tokens = attempt("C", cond_cd(True))
            k = max(1, round(c_tokens / sample_tokens)) if sample_tokens and c_tokens else 3

            def cond_b(start, t0):
                a, recs = run_ensemble(p, llm, k, s)
                record("B", a.ranking[0], start, t0, k=k, samples_ok=len(recs), sample_recommendations=", ".join(recs))

            attempt("B", cond_b)
            attempt("D", cond_cd(False))
    return pd.DataFrame(rows)


def report(df: pd.DataFrame, llm: LLM) -> str:
    ok = df[df.error.isna()]
    agg = []
    for cond in "ABCD":
        d = ok[ok.condition == cond]
        if d.empty:
            continue
        acc, lo, hi = bootstrap_ci(d.correct.astype(float)) if len(d) > 1 else (d.correct.mean(),) * 3
        row = {"condition": cond, "runs": len(d), "failed": int((df.condition == cond).sum() - len(d)),
               "accuracy": acc, "ci_low": lo, "ci_high": hi, "dominated_errors": int(d.dominated_recommended.sum()),
               "mean_tokens": d.tokens.mean(), "mean_seconds": d.seconds.mean()}
        if cond in "CD":
            row |= {"analyst_flags": int(d.analyst_flags.sum()), "no_fact_claims": int(d.no_fact_claims.sum()),
                    "flags_on_no_fact": int(d.flags_on_no_fact.sum()),
                    "conformity": f"{int(d.conformity_events.sum())}/{int(d.conformity_opps.sum())}"}
        agg.append(row)
    agg = pd.DataFrame(agg)
    stab = ok.groupby(["condition", "scenario"]).recommendation.nunique()
    multi = ok.groupby(["condition", "scenario"]).size() > 1
    stab_txt = ("not measured (1 seed)" if not multi.any() else
                "; ".join(f"{c}: {int((stab[multi].xs(c) == 1).sum())}/{int(multi.xs(c).sum())} scenarios stable"
                          for c in "ABCD" if c in stab.index.get_level_values(0)))
    s = llm.run.stats()
    cols = [c for c in df.columns if c not in ("error",)]
    return "\n".join([
        "## Phase 3 ablations", "",
        md_table(agg.fillna("")), "",
        f"- Ranking stability across seeds: {stab_txt}",
        f"- Parse failure rate (all calls): {s.failed_attempts.sum() / s.attempts.sum():.1%}",
        "- conformity = agent abandoned a preferred option that matched the reference / opportunities "
        "(in D the agents see no one, so changes there are self-driven drift)",
        "- B samples at actor temperature (0.7); at the scorer's 0.1 the K samples would be near copies.", "",
        "### Per-call parse failures", "", md_table(s[["tag", "attempts", "failed_attempts", "parse_fail_rate"]]), "",
        "### All rows", "", md_table(df[cols].fillna("")), "",
        *([f"Errors: {e}" for e in df.error.dropna()]),
    ])
