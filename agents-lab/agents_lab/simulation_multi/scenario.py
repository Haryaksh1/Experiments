"""Pluggable three-seat scenarios. Python, not the LLM, applies the rules.

A new scenario (e.g. a negotiation) implements the Scenario protocol: the rules text agents see, the
schema and task for each round's private decision, how decisions turn into an outcome, what each seat
observes, and the scenario's own metrics.
"""
from typing import Literal, Protocol

import numpy as np
from pydantic import BaseModel, Field


class Scenario(Protocol):
    name: str
    rounds: int

    def rules(self) -> str: ...
    def decision_schema(self) -> type[BaseModel]: ...
    def decision_task(self, t: int) -> str: ...
    def apply(self, t: int, decisions: dict[str, BaseModel]) -> dict: ...
    def outcome_text(self, t: int, outcome: dict) -> str: ...
    def metrics(self, log: list[dict]) -> dict: ...


class Contribution(BaseModel):
    reason: str = Field(max_length=120)  # reason first, then the number
    contribution: Literal[tuple(range(11))]


class PublicGoods:
    """Repeated three-player public goods game: each round every player gets `endowment` tokens and
    privately contributes 0..endowment; the pot is multiplied and split equally."""
    name = "public_goods"

    def __init__(self, rounds: int = 8, endowment: int = 10, multiplier: float = 1.5):
        if endowment != 10:
            raise ValueError("decision schema is 0-10; change Contribution to support another endowment")
        self.rounds, self.endowment, self.multiplier = rounds, endowment, multiplier

    def rules(self) -> str:
        return (f"Game rules: {self.rounds} rounds. Each round every player gets {self.endowment} tokens and "
                f"privately chooses how many (0-{self.endowment}) to put into a shared pot. The pot is multiplied "
                f"by {self.multiplier:g} and split equally among the 3 players; tokens you keep are yours. "
                "After each round everyone sees every contribution.")

    def decision_schema(self) -> type[BaseModel]:
        return Contribution

    def decision_task(self, t: int) -> str:
        return (f"Task: round {t}. Privately choose how many tokens (0-{self.endowment}) you put into the pot, "
                "with a short reason first.")

    def payoffs(self, contributions: dict[str, int]) -> dict[str, float]:
        share = sum(contributions.values()) * self.multiplier / len(contributions)
        return {k: self.endowment - c + share for k, c in contributions.items()}

    def apply(self, t: int, decisions: dict[str, BaseModel]) -> dict:
        c = {k: int(d.contribution) for k, d in decisions.items()}
        return {"round": t, "contributions": c, "pot": sum(c.values()) * self.multiplier, "payoffs": self.payoffs(c)}

    def outcome_text(self, t: int, outcome: dict) -> str:
        c = ", ".join(f"{k} {v}" for k, v in outcome["contributions"].items())
        p = ", ".join(f"{k} {v:.1f}" for k, v in outcome["payoffs"].items())
        return f"Round {t} result: contributions {c}; pot {outcome['pot']:.1f}; payoffs {p}."

    def metrics(self, log: list[dict]) -> dict:
        rounds = [r["outcome"]["contributions"] for r in log]
        names = list(rounds[0])
        mean = [float(np.mean(list(r.values()))) for r in rounds]
        slope = float(np.polyfit(range(1, len(mean) + 1), mean, 1)[0]) if len(mean) > 1 else 0.0
        totals = {n: round(sum(r["outcome"]["payoffs"][n] for r in log), 1) for n in names}
        return {"mean_contribution_by_round": [round(m, 2) for m in mean], "mean_contribution": round(float(np.mean(mean)), 2),
                "trend_per_round": round(slope, 3), "first_round_mean": mean[0], "last_round_mean": mean[-1],
                "contributions": {n: [r[n] for r in rounds] for n in names}, "total_payoffs": totals}


# --- fixed-strategy baselines (Python only; they post a truthful templated message) ----------------

class Bot:
    is_llm = False

    def __init__(self, name: str, kind: Literal["always", "never", "conditional"]):
        self.name, self.kind = name, kind

    def intended(self, t: int, history: list[dict]) -> int:
        if self.kind == "always":
            return 10
        if self.kind == "never":
            return 0
        if not history:  # conditional cooperator: start cooperative, then match the others' last average
            return 10
        others = [v for k, v in history[-1]["contributions"].items() if k != self.name]
        return int(round(float(np.mean(others))))

    def chat(self, t: int, history: list[dict]) -> tuple[str, int]:
        x = self.intended(t, history)
        return f"I will put {x} tokens into the pot this round.", x

    def decide(self, t: int, history: list[dict]) -> Contribution:
        return Contribution(reason=f"fixed strategy: {self.kind}", contribution=self.intended(t, history))

