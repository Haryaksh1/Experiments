"""Step 2: the only multi-agent step. Exactly three agents (Advocate, Skeptic, Analyst) with their
own system prompts and their own memory of their previous turns, conversing via core.run_conversation.

Claim ids are assigned in Python (e.g. SKE1.2 = Skeptic, round 1, claim 2) so agents can accept,
reject or flag each other's claims by id; ids are validated against what the agent was shown.
"""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents_lab.core.conversation import Turn
from agents_lab.core.llm import LLM
from agents_lab.decision_single.schemas import Problem

ROLES = {
    "Advocate": ("You are the Advocate on a three-member decision panel. Argue for the option you currently think "
                 "is strongest, using the facts. Switch only if the evidence convinces you. Reply with JSON only."),
    "Skeptic": ("You are the Skeptic on a three-member decision panel. Attack the weaknesses of every option and "
                "question the shared assumptions. Still name the option you would pick if forced. Reply with JSON only."),
    "Analyst": ("You are the Analyst on a three-member decision panel. Check each claim of the others against the "
                "facts in the brief and flag every claim the facts do not support. Name the option the facts favor. "
                "Reply with JSON only."),
}
PREFIX = {"Advocate": "ADV", "Skeptic": "SKE", "Analyst": "ANA"}
CLAIM_ID = re.compile(r"\b(?:ADV|SKE|ANA)\d+\.\d+\b")


# Short limits on purpose: phi3 fills strings and lists up to their maximum, which overflows max_tokens.
class Claim(BaseModel):
    text: str = Field(max_length=100)
    facts: list[int] = Field(max_length=3)  # supporting fact numbers; empty = unsupported


class Ref(BaseModel):
    claim: str = Field(max_length=10)
    reason: str = Field(max_length=80)


class DebateTurn(BaseModel):
    preferred_option: str  # "if forced to pick"; used for the conformity metric
    position: str = Field(max_length=120)
    claims: list[Claim] = Field(min_length=1, max_length=2)
    accepts: list[Ref] = Field(max_length=1)
    rejects: list[Ref] = Field(max_length=1)


class AnalystTurn(DebateTurn):
    flags: list[Ref] = Field(max_length=2)  # claims the facts don't support


def turn_schema(p: Problem, analyst: bool, valid_ids: set[str]) -> type[DebateTurn]:
    """Claim references are an enum of the ids this agent was shown, and fact numbers an enum of 1..n,
    so the grammar can't invent either; with nothing shown (round 0, or isolated agents) the reference
    lists are forced empty."""
    class C(Claim):
        facts: list[Literal[tuple(range(1, len(p.facts) + 1))]] = Field(max_length=3)

    if valid_ids:
        class R(Ref):
            claim: Literal[tuple(sorted(valid_ids))]
        ref, k = R, 1
    else:
        ref, k = Ref, 0

    class Checked(AnalystTurn if analyst else DebateTurn):
        model_config = ConfigDict(title="AnalystTurn" if analyst else "DebateTurn")
        preferred_option: Literal[tuple(p.options)]
        claims: list[C] = Field(min_length=1, max_length=2)
        accepts: list[ref] = Field(max_length=k)
        rejects: list[ref] = Field(max_length=k)
        if analyst:
            flags: list[ref] = Field(max_length=2 * k)

        @model_validator(mode="after")
        def _check(self):
            if both := {r.claim for r in self.accepts} & {r.claim for r in self.rejects}:
                raise ValueError(f"claims {sorted(both)} are both accepted and rejected; pick one")
            return self

    return Checked


def claim_ids(agent: str, round: int, t: DebateTurn) -> list[str]:
    return [f"{PREFIX[agent]}{round}.{i}" for i in range(1, len(t.claims) + 1)]


def fmt_turn(agent: str, round: int, t: DebateTurn) -> str:
    lines = [f"{agent} (round {round}, prefers {t.preferred_option}): {t.position}"]
    for cid, c in zip(claim_ids(agent, round, t), t.claims):
        lines.append(f"  {cid}: {c.text} [" + (", ".join(f"F{f}" for f in c.facts) or "no fact") + "]")
    for label, refs in (("accepts", t.accepts), ("rejects", t.rejects),
                        ("flags as unsupported", getattr(t, "flags", []))):
        if refs:
            lines.append(f"  {label}: " + "; ".join(f"{r.claim} ({r.reason})" for r in refs))
    return "\n".join(lines)


def summarize_round(turns: list[Turn]) -> str:
    """Deterministic rolling-summary chunk for one round (no LLM)."""
    return "\n".join(fmt_turn(t.agent, t.round, t.content) for t in turns)


class Debater:
    """One panel member: own system prompt (role + goal) and own memory of its previous turns."""

    def __init__(self, role: str, problem: Problem, brief: str, llm: LLM, seed: int | None = None):
        self.name, self.system, self.p, self.brief, self.llm, self.seed = role, ROLES[role], problem, brief, llm, seed
        self.history: list[DebateTurn] = []

    def respond(self, round: int, summary: str, others_last: dict[str, BaseModel]) -> DebateTurn:
        analyst = self.name == "Analyst"
        others = "\n".join(fmt_turn(a, round - 1, t) for a, t in others_last.items())
        valid = set(CLAIM_ID.findall(summary)) | set(CLAIM_ID.findall(others))
        own = fmt_turn(self.name, round - 1, self.history[-1]) if self.history else "none"
        if round == 0:
            task = ("Task: state your position independently: the option you prefer if forced to pick, your "
                    "position, and 1-2 claims, each with the fact numbers that support it (empty if none). "
                    "Leave accepts, rejects" + (" and flags" if analyst else "") + " empty.")
        else:
            task = ("Task: respond to the others' latest turns. Give the option you now prefer, your position, 1-2 "
                    "new claims with fact numbers, and at most one of their claims you accept and one you reject "
                    "(by claim id, a different claim each), with short reasons.")
            if analyst:
                task += " In flags, list claim ids the facts do not support, with the reason."
        user = (f"{self.brief}\n\nEarlier discussion:\n{summary or 'none'}\n\nOthers' latest turns:\n{others or 'none'}"
                f"\n\nYour previous turn:\n{own}\n\n{task}")
        t = self.llm.structured(self.system, user, turn_schema(self.p, analyst, valid), tag=f"turn_{self.name.lower()}",
                                seed=self.seed, max_tokens=450)
        self.history.append(t)
        return t

