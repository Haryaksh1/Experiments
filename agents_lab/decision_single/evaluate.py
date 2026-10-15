"""Phase 1 eval: reference agreement, dominated-option errors, seed stability, parse failures, time."""
from pathlib import Path

import pandas as pd

from agents_lab.core.llm import LLM, LLMFailed
from agents_lab.core.stats import bootstrap_ci
from agents_lab.core.trace import md_table
from agents_lab.decision_single.agent import DecisionAgent
from agents_lab.decision_single.schemas import Problem

SCENARIOS = Path(__file__).resolve().parent.parent / "evals" / "decision"


def load_scenarios(folder: Path = SCENARIOS, limit: int | None = None) -> list[Problem]:
    return [Problem.from_yaml(f) for f in sorted(folder.glob("*.yaml"))][:limit]


def evaluate(problems: list[Problem], llm: LLM, stability: int = 4, n_seeds: int = 3) -> pd.DataFrame:
    """Seed 0: full run (clarify, score, memo). Extra seeds on the first `stability` scenarios
    re-score with the same clarification, so stability measures the scorer."""
    seeds = [llm.cfg.seed + k for k in range(n_seeds)]
    out_dir = llm.run.dir / "results"
    out_dir.mkdir(exist_ok=True)
    rows = []
    for i, p in enumerate(problems):
        clar = None
        for s in seeds if i < stability else seeds[:1]:
            row = dict(scenario=p.id, category=p.reference.category, seed=s, full_run=s == seeds[0],
                       reference=p.reference.best)
            try:
                r = DecisionAgent(llm, seed=s).run(p, clarification=clar, memo=s == seeds[0])
            except LLMFailed as e:
                rows.append({**row, "error": str(e)})
                continue
            clar = r.clarification
            llm.run.log("decision_result", **r.to_dict())
            (out_dir / f"{p.id}_seed{s}.md").write_text(r.to_markdown(), encoding="utf-8")
            a = r.analysis
            rows.append({**row, "recommendation": r.recommendation, "correct": r.recommendation == p.reference.best,
                         "dominated_recommended": r.recommendation in p.reference.dominated,
                         "ref_dominated_detected": all(d in a.dominated for d in p.reference.dominated)
                         if p.reference.dominated else None,
                         "ranking": " > ".join(a.ranking), "margin": round(a.margin, 2),
                         "seconds": round(r.seconds, 1), "error": None})
    return pd.DataFrame(rows)


def report(df: pd.DataFrame, llm: LLM) -> str:
    ok = df[df.error.isna()]
    first = ok[ok.full_run]
    acc, lo, hi = bootstrap_ci(first.correct.astype(float)) if len(first) else (float("nan"),) * 3
    by_cat = first.groupby("category").correct.agg(["mean", "count"]).reset_index()
    det = first.ref_dominated_detected.dropna()
    multi = ok.groupby("scenario").filter(lambda g: len(g) > 1).groupby("scenario")
    stab = pd.DataFrame({"seeds": multi.size(), "top1_stable": multi.recommendation.nunique() == 1,
                         "ranking_stable": multi.ranking.nunique() == 1,
                         "recommendations": multi.recommendation.agg(lambda s: ", ".join(s))}).reset_index()
    s = llm.run.stats()
    pfr = s.failed_attempts.sum() / s.attempts.sum() if len(s) else float("nan")
    lines = [
        "## Phase 1 results", "",
        f"- Scenarios: {df.scenario.nunique()}, runs: {len(df)}, failed runs: {int(df.error.notna().sum())}",
        f"- Agreement with reference (seed {llm.cfg.seed}): {acc:.0%} (95% bootstrap CI {lo:.0%}-{hi:.0%}, n={len(first)})",
        f"- Dominated option recommended: {int(ok.dominated_recommended.sum())} of {len(ok)} runs",
        f"- Reference-dominated option also dominated in the model's scores: {int(det.sum())} of {len(det)} scenarios",
        f"- Top-1 stable across seeds: {int(stab.top1_stable.sum())} of {len(stab)} scenarios; "
        f"full ranking stable: {int(stab.ranking_stable.sum())} of {len(stab)}",
        f"- Parse failure rate (failed attempts / attempts): {pfr:.1%}",
        f"- Time per scenario, full run: {first.seconds.mean():.0f} s; extra-seed re-score: "
        f"{ok[~ok.full_run].seconds.mean():.0f} s", "",
        "### Agreement by category", "", md_table(by_cat), "",
        "### Seed stability", "", md_table(stab) if len(stab) else "(none)", "",
        "### All runs", "",
        md_table(df.drop(columns=[c for c in ["full_run"] if c in df]).fillna("")), "",
    ]
    return "\n".join(lines)
