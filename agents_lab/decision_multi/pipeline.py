"""Phase 3 pipeline: exactly three agent steps; only Step 2 is multi-agent.

Step 1 Framer (one agent) -> brief.
Step 2 Deliberation (exactly three agents conversing, R rounds after an independent round 0).
Step 3 Judge (one agent) -> Phase 1 rubric scores citing the arguments that changed them;
Python computes the ranking and sensitivity exactly as in Phase 1.
"""
import time
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents_lab.core.conversation import Turn, compress, run_conversation
from agents_lab.core.llm import LLM, BudgetExceeded
from agents_lab.core.trace import md_table
from agents_lab.decision_single.agent import DecisionAgent
from agents_lab.decision_single.compute import Analysis, analyze
from agents_lab.decision_single.schemas import Cell, Line, Problem, score_schema
from agents_lab.decision_multi.deliberation import CLAIM_ID, Debater, claim_ids, fmt_turn, summarize_round

FRAMER_SYSTEM = ("You are the Framer. You turn a decision problem into a clear, faithful brief for a decision "
                 "panel. Reply with JSON only.")
JUDGE_SYSTEM = ("You are the Judge. You score the options using the facts, the brief and the panel's arguments, "
                "and you say which arguments changed your scores. Reply with JSON only.")
DEBATERS = ("Advocate", "Skeptic", "Analyst")


class OptionSummary(BaseModel):
    option: str
    summary: str = Field(max_length=120)


class Brief(BaseModel):
    option_summaries: list[OptionSummary]
    assumptions: list[Line] = Field(max_length=3)
    open_questions: list[Line] = Field(max_length=3)

    def text(self, p: Problem) -> str:
        """Fact ids per option come from Python (Problem.facts_about), not from the model."""
        return "\n".join(["Framer's brief:", *[f"- {s.option}: {s.summary} [facts: " + ", ".join(
                              f"F{f}" for f in p.facts_about(s.option)) + "]" for s in self.option_summaries],
                          "Assumptions:", *([f"A{i}. {a}" for i, a in enumerate(self.assumptions, 1)] or ["- none"]),
                          "Open questions:", *([f"Q{i}. {q}" for i, q in enumerate(self.open_questions, 1)]
                                               or ["- none"])])


def brief_schema(p: Problem) -> type[Brief]:
    class S(OptionSummary):
        option: Literal[tuple(p.options)]

    class Checked(Brief):
        model_config = ConfigDict(title="Brief")
        option_summaries: list[S] = Field(min_length=len(p.options), max_length=len(p.options))

        @model_validator(mode="after")
        def _check(self):
            if sorted(s.option for s in self.option_summaries) != sorted(p.options):
                raise ValueError(f"give exactly one summary per option: {', '.join(p.options)}")
            return self

    return Checked


def frame(p: Problem, llm: LLM, seed: int | None = None) -> Brief:
    b = llm.structured(FRAMER_SYSTEM, f"{p.prompt()}\n\nTask: write the brief: one short summary per option (under "
                       "20 words, from its facts), up to 3 explicit assumptions, and up to 3 open questions.",
                       brief_schema(p), tag="framer", seed=seed, max_tokens=400)
    llm.run.log("brief", problem_id=p.id, brief=b.model_dump())
    return b


@dataclass
class PipelineResult:
    problem: Problem
    visible: bool
    brief: Brief
    turns: list[Turn]
    cells: dict[str, dict[str, Cell]]
    cited: dict[str, list[str]]  # criterion -> claim ids the Judge says changed its scores
    analysis: Analysis
    seconds: float

    @property
    def recommendation(self) -> str:
        return self.analysis.ranking[0]

    def all_claims(self) -> dict[str, tuple[str, list[int]]]:
        """claim id -> (text, fact numbers)"""
        return {cid: (c.text, c.facts) for t in self.turns
                for cid, c in zip(claim_ids(t.agent, t.round, t.content), t.content.claims)}

    def to_markdown(self) -> str:
        a = self.analysis
        rank = a.ev.to_frame("expected").assign(low=a.ev_low, high=a.ev_high).loc[a.ranking].round(2)
        out = [f"# Panel decision: {self.problem.question}", "",
               f"**Recommendation: {self.recommendation}** (margin {a.margin:.2f}; agents "
               f"{'see each other' if self.visible else 'isolated (ablation D)'})", "",
               "## Step 1: brief", "", self.brief.text(self.problem), "", "## Step 2: deliberation", ""]
        for r in sorted({t.round for t in self.turns}):
            out += [f"### Round {r}", "", "```", summarize_round([t for t in self.turns if t.round == r]), "```", ""]
        out += ["## Step 3: judge", "", "Arguments the Judge cited per criterion: "
                + "; ".join(f"{c}: {', '.join(ids) or 'none'}" for c, ids in self.cited.items()), "",
                md_table(rank.reset_index(names="option")), "", a.text(), ""]
        return "\n".join(out)


def judge(p: Problem, llm: LLM, brief: Brief, turns: list[Turn], seed: int | None = None):
    """Phase 1 rubric scoring with the brief and the deliberation summary as context."""
    summary = "\n".join(fmt_turn(t.agent, t.round, t.content) for t in turns)
    known = tuple(sorted(set(CLAIM_ID.findall(summary))))  # every turn has >= 1 claim, so never empty

    class JudgeScores(score_schema(p)):
        model_config = ConfigDict(title="JudgeScores")
        cited_claims: list[Literal[known]] = Field(max_length=4)  # enum: only real claim ids

    suffix = (" Also give cited_claims: the ids of the panel's claims (e.g. SKE1.2) that changed your scores on "
              "this criterion, or an empty list if none did.")
    agent = DecisionAgent(llm, seed=seed, system=JUDGE_SYSTEM)
    try:
        cells = agent.score(p, f"{brief.text(p)}\n\nPanel deliberation:\n{summary}", tag="judge", schema=JudgeScores,
                            task_suffix=suffix)
    except BudgetExceeded:  # older rounds are compressed first, the last round kept verbatim (logged)
        last = max(t.round for t in turns)
        older = compress(llm, "\n".join(fmt_turn(t.agent, t.round, t.content) for t in turns if t.round < last))
        recent = "\n".join(fmt_turn(t.agent, t.round, t.content) for t in turns if t.round == last)
        cells = agent.score(p, f"{brief.text(p)}\n\nPanel deliberation (older rounds summarized):\n{older}\n{recent}",
                            tag="judge", schema=JudgeScores, task_suffix=suffix)
    cited = {c: r.cited_claims for c, r in agent.memory["raw"].items()}
    return cells, cited


def run_pipeline(p: Problem, llm: LLM, rounds: int = 2, visible: bool = True,
                 seed: int | None = None) -> PipelineResult:
    t0 = time.perf_counter()
    brief = frame(p, llm, seed)                                                         # Step 1
    debate_brief = f"{p.prompt()}\n\n{brief.text(p)}"
    agents = [Debater(role, p, debate_brief, llm, seed) for role in DEBATERS]
    assert len(agents) == 3
    turns = run_conversation(agents, rounds, llm, summarize_round, visible=visible)    # Step 2
    cells, cited = judge(p, llm, brief, turns, seed)                                   # Step 3
    a = analyze(cells, p.weights)
    llm.run.log("judge", problem_id=p.id, visible=visible, cited=cited, ranking=a.ranking,
                ev=a.ev.round(3).to_dict())
    return PipelineResult(p, visible, brief, turns, cells, cited, a, time.perf_counter() - t0)

