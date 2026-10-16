from pydantic import BaseModel

from agents_lab.core.conversation import run_conversation
from agents_lab.core.llm import BudgetExceeded


class Say(BaseModel):
    text: str


class Echo:
    """Records exactly what it was shown each round."""

    def __init__(self, name, limit=None):
        self.name, self.limit, self.seen = name, limit, []

    def respond(self, round, summary, others_last):
        if self.limit and len(summary) > self.limit:
            raise BudgetExceeded("too long")
        self.seen.append((round, summary, {k: v.text for k, v in others_last.items()}))
        return Say(text=f"{self.name}{round}")


def chunk(turns):
    return " ".join(t.content.text for t in turns)


def test_rounds_visibility_and_summary(make_llm):
    llm, _ = make_llm([])
    agents = [Echo("a"), Echo("b"), Echo("c")]
    turns = run_conversation(agents, rounds=2, llm=llm, summarize=chunk)
    assert [(t.agent, t.round) for t in turns] == [(n, r) for r in range(3) for n in "abc"]
    a = agents[0].seen
    assert a[0] == (0, "", {})                              # independent opening
    assert a[1] == (1, "", {"b": "b0", "c": "c0"})          # previous round, not own, not same round
    assert a[2] == (2, "a0 b0 c0", {"b": "b1", "c": "c1"})  # summary covers rounds < r-1


def test_invisible_agents_see_nothing(make_llm):
    llm, _ = make_llm([])
    agents = [Echo("a"), Echo("b"), Echo("c")]
    run_conversation(agents, rounds=3, llm=llm, summarize=chunk, visible=False)
    assert all(s == "" and o == {} for ag in agents for _, s, o in ag.seen)


def test_overflow_summarizes_and_logs(make_llm):
    llm, backend = make_llm(['{"summary": "short"}'] * 5)
    agents = [Echo("a", limit=10), Echo("b", limit=10), Echo("c", limit=10)]
    run_conversation(agents, rounds=3, llm=llm, summarize=lambda ts: "long summary text " * 3)
    assert any(e["event"] == "summarized" for e in llm.run.events)
    assert agents[0].seen[-1][1].startswith("short")  # the compressed summary is what agents saw
