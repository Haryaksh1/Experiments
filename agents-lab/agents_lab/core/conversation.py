"""R rounds among N agents with a rolling summary and a context budget check.

Round 0: every agent states a position independently. Rounds 1..R: every agent sees the
rolling summary (rounds < r-1) plus the previous-round turn of each other agent.
Rounds are simultaneous, so speaking order inside a round does not leak information.
With visible=False agents see nothing from each other (ablation D); they keep their own
history in their own state.
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from agents_lab.core.llm import LLM, BudgetExceeded


@dataclass
class Turn:
    agent: str
    round: int
    content: BaseModel


class ConvAgent(Protocol):
    name: str

    def respond(self, round: int, summary: str, others_last: dict[str, BaseModel]) -> BaseModel: ...


class Summary(BaseModel):
    summary: str = Field(max_length=1200)


def compress(llm: LLM, text: str, tag: str = "summarize") -> str:
    out = llm.structured("You compress discussion notes. Keep every option name, each speaker's position "
                         "and their main claims. At most 120 words.", text, Summary, tag=tag, judge=True,
                         max_tokens=300)
    llm.run.log("summarized", tag=tag, before_chars=len(text), after_chars=len(out.summary))
    return out.summary


def run_conversation(agents: list[ConvAgent], rounds: int, llm: LLM,
                     summarize: Callable[[list[Turn]], str], visible: bool = True) -> list[Turn]:
    """`summarize` turns one round's turns into a short text chunk (deterministic, no LLM)."""
    turns: list[Turn] = []
    summary = ""
    for r in range(rounds + 1):
        if r >= 2:
            summary = (summary + "\n" + summarize([t for t in turns if t.round == r - 2])).strip()
        last = {t.agent: t.content for t in turns if t.round == r - 1}
        for a in agents:
            others = {k: v for k, v in last.items() if k != a.name} if visible else {}
            shared = summary if visible else ""
            try:
                out = a.respond(r, shared, others)
            except BudgetExceeded:
                if not shared:
                    raise  # nothing older left to summarize
                summary = shared = compress(llm, shared)
                out = a.respond(r, shared, others)
            turns.append(Turn(a.name, r, out))
            llm.run.log("turn", agent=a.name, round=r, visible=visible, content=out.model_dump())
    return turns
