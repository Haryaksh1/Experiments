"""Phase 1: one decision agent. clarify -> score (one call per option) -> Python analysis -> memo.

Prompt layout for the prefix cache: problem text, then clarification context, then the task.
Every score call and the memo call share the first two parts verbatim.
"""
import time
from dataclasses import dataclass

from agents_lab.core.llm import LLM
from agents_lab.decision_single.compute import Analysis, analyze
from agents_lab.decision_single.schemas import Cell, Clarification, Memo, Problem, score_schema
from agents_lab.core.trace import md_table

SYSTEM = ("You are a careful decision analyst. Use only the facts given; when you must assume something, "
          "say so. Reply with JSON only.")


def score_task(p: Problem, criterion) -> str:
    facts = "; ".join(f"{o}: " + ", ".join(f"F{i}" for i in p.facts_about(o)) for o in p.options)
    return (f'Task: score every option on the criterion "{criterion.name}" ({criterion.description}). '
            f"Compare the options with each other. Relevant facts per option: {facts}. For each option give: facts "
            "(the numbers of the facts you used, e.g. [1, 4]), low, mid and high (integers 0-10 in increasing "
            "order: low <= mid <= high; 10 = best for the decision-maker), a justification under 20 words, and "
            "basis \"fact\" (or \"assumption\" with facts [] if no fact applies).")


@dataclass
class DecisionResult:
    problem: Problem
    seed: int | None
    clarification: Clarification
    cells: dict[str, dict[str, Cell]]
    analysis: Analysis
    memo: Memo | None
    seconds: float

    @property
    def recommendation(self) -> str:
        return self.analysis.ranking[0]

    def to_dict(self) -> dict:
        a = self.analysis
        return {"problem_id": self.problem.id, "seed": self.seed, "recommendation": self.recommendation,
                "ranking": a.ranking, "ev": a.ev.round(3).to_dict(), "margin": round(a.margin, 3),
                "dominated": a.dominated, "clarification": self.clarification.model_dump(),
                "cells": {o: {c: v.model_dump() for c, v in r.items()} for o, r in self.cells.items()},
                "sensitivity": a.sensitivity.round(3).to_dict("records"),
                "memo": self.memo.model_dump() if self.memo else None, "seconds": round(self.seconds, 1)}

    def to_markdown(self) -> str:
        a, p, m = self.analysis, self.problem, self.memo
        rank = a.ev.to_frame("expected").assign(low=a.ev_low, high=a.ev_high).loc[a.ranking].round(2)
        out = [f"# Decision memo: {p.question}", "",
               f"**Recommendation: {self.recommendation}** (margin {a.margin:.2f} on a 0-10 scale"
               + (f"; model confidence: {m.confidence})" if m else ")"), ""]
        if m:
            out += [m.rationale, "", "## Key risks", *[f"- {r}" for r in m.key_risks], "",
                    "## Evidence that would change the decision", *[f"- {e}" for e in m.evidence_that_would_change], ""]
        out += ["## Ranking (computed in Python)", "", md_table(rank.reset_index(names="option")), "",
                "## Sensitivity: smallest single changes that flip the top choice", "",
                md_table(a.sensitivity.groupby("change").head(3).round(2)), ""]
        if a.dominated:
            out += [f"Dominated on expected scores: {', '.join(a.dominated)}", ""]
        out += ["## Clarification", "", self.clarification.context(), "", "## Scores", "",
                "| option | criterion | low | mid | high | basis | justification |", "|---|---|---|---|---|---|---|"]
        out += [f"| {o} | {c} | {v.low} | {v.mid} | {v.high} | {v.basis} | {v.justification} |"
                for o, r in self.cells.items() for c, v in r.items()]
        return "\n".join(out) + "\n"


class DecisionAgent:
    """Own system prompt (role + goal), own memory of what it produced, no tools."""

    def __init__(self, llm: LLM, seed: int | None = None, system: str = SYSTEM, low_temperature_scoring: bool = True):
        self.llm, self.seed, self.system = llm, seed, system
        self.low_temperature_scoring = low_temperature_scoring  # False only for ensemble sampling (Phase 3 B)
        self.memory: dict = {}

    def clarify(self, p: Problem) -> Clarification:
        user = (f"{p.prompt()}\n\nTask: list up to 4 pieces of missing information that matter for this decision, "
                "and up to 4 assumptions you will make to fill the gaps. One short line each.")
        c = self.llm.structured(self.system, user, Clarification, tag="clarify", seed=self.seed, max_tokens=350)
        self.memory["clarification"] = c
        return c

    def score(self, p: Problem, context: str, tag: str = "score", schema=None,
              task_suffix: str = "") -> dict[str, dict[str, Cell]]:
        """One scorer call per criterion, all options compared in that call (low temperature).
        `context` sits between problem and task. `schema` may extend score_schema(p) with extra fields;
        raw replies are kept in memory["raw"][criterion]."""
        schema = schema or score_schema(p)
        cells, raw = {o: {} for o in p.options}, {}
        for crit in p.criteria:
            user = f"{p.prompt()}\n\n{context}\n\n{score_task(p, crit)}{task_suffix}"
            r = self.llm.structured(self.system, user, schema, tag=tag, judge=self.low_temperature_scoring,
                                    seed=self.seed, max_tokens=450)
            raw[crit.name] = r
            for i, o in enumerate(p.options):
                cells[o][crit.name] = getattr(r, f"o{i}")
        self.memory["raw"] = raw
        self.memory["scores"] = cells
        return cells

    def memo(self, p: Problem, context: str, a: Analysis) -> Memo:
        user = (f"{p.prompt()}\n\n{context}\n\nResults computed in Python (weighted expected score 0-10; range is "
                f"all-low to all-high):\n{a.text()}\n\nTask: write a decision memo recommending \"{a.ranking[0]}\". "
                "Fields: rationale (under 60 words, cite fact ids), confidence (low, medium or high), key_risks "
                "(up to 3), evidence_that_would_change (up to 3 findings that would change the decision).")
        m = self.llm.structured(self.system, user, Memo, tag="memo", seed=self.seed, max_tokens=450)
        self.memory["memo"] = m
        return m

    def run(self, p: Problem, clarification: Clarification | None = None, memo: bool = True) -> DecisionResult:
        t0 = time.perf_counter()
        c = clarification or self.clarify(p)
        ctx = c.context()
        cells = self.score(p, ctx)
        a = analyze(cells, p.weights)
        m = self.memo(p, ctx, a) if memo else None
        return DecisionResult(p, self.seed, c, cells, a, m, time.perf_counter() - t0)
