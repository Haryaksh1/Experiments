"""Phase 2 persona mode: one generative agent living through a simulated day.

Loop per plan step: store pending memories (one importance call), maybe reflect, then act.
New memories (the last action + new events) are stored together at the start of the next step.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

from agents_lab.core.llm import LLM
from agents_lab.simulation_single.memory import Kind, Memory, MemoryStream

# No \d: Ollama's schema-to-grammar converter can't parse it and the model runner crashes.
HHMM = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


class Persona(BaseModel):
    name: str
    age: int
    description: str
    backstory: list[str]

    @classmethod
    def from_yaml(cls, path):
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))


class Block(BaseModel):
    start: str = Field(pattern=HHMM)
    end: str = Field(pattern=HHMM)
    activity: str = Field(max_length=100)


class DayPlan(BaseModel):
    blocks: list[Block] = Field(min_length=3, max_length=5)


class Step(BaseModel):
    time: str = Field(pattern=HHMM)
    action: str = Field(max_length=100)


class Steps(BaseModel):
    steps: list[Step] = Field(min_length=4, max_length=10)

    @model_validator(mode="after")
    def _ordered(self):
        times = [s.time for s in self.steps]
        if times != sorted(times) or len(set(times)) != len(times):
            raise ValueError("step times must be strictly increasing")
        return self


class Act(BaseModel):
    action: str = Field(max_length=150)
    changes_plan: bool
    reason: str = Field(max_length=150)


class Insight(BaseModel):
    insight: str = Field(max_length=160)
    evidence: list[int] = Field(min_length=1, max_length=5)


class Reflection(BaseModel):
    insights: list[Insight] = Field(min_length=1, max_length=3)


class Answer(BaseModel):
    memories_used: list[int] = Field(max_length=3)  # evidence first, as in Phase 1 scoring
    answer: str = Field(max_length=400)


def fmt(mems: list[Memory]) -> str:
    return "\n".join(f"[{m.id}] ({m.created:%H:%M}) {m.text}" for m in mems) or "(none)"


class GenerativeAgent:
    def __init__(self, persona: Persona, llm: LLM, now: datetime, reflect_threshold: int = 150, k: int = 8,
                 memory_budget: int = 600, weights: tuple[float, float, float] = (1.0, 1.0, 1.0)):
        self.persona, self.llm, self.now = persona, llm, now
        self.reflect_threshold, self.k, self.memory_budget = reflect_threshold, k, memory_budget
        self.mem = MemoryStream(llm, persona.name, weights=weights)
        self.pending: list[tuple[Kind, str]] = []
        self.steps: list[Step] = []
        self.reflections = 0

    @property
    def system(self) -> str:
        p = self.persona
        return f"You are {p.name}, age {p.age}. {p.description} Stay in character. Reply with JSON only."

    def at(self, hhmm: str) -> datetime:
        h, m = map(int, hhmm.split(":"))
        return self.now.replace(hour=h, minute=m, second=0, microsecond=0)

    def seed(self):
        """Backstory becomes the first memories, dated the day before."""
        self.mem.add_many([("observation", b) for b in self.persona.backstory], self.now - timedelta(days=1),
                          count_for_reflection=False)

    def observe(self, text: str):
        self.pending.append(("observation", text))

    def commit(self):
        self.mem.add_many(self.pending, self.now)
        self.pending = []
        if self.mem.importance_since_reflection >= self.reflect_threshold:
            self.reflect()

    def plan_day(self, wake: str, sleep: str) -> list[Step]:
        mems = self.mem.retrieve(f"{self.persona.name} plans goals priorities today", self.now, self.k,
                                 self.memory_budget)
        p = self.llm.structured(self.system, f"Relevant memories:\n{fmt(mems)}\n\nToday is {self.now:%A %d %B %Y}. "
                                f"Task: make a broad plan for today from {wake} to {sleep} in 3 to 5 blocks "
                                "(start, end as HH:MM, activity).", DayPlan, tag="plan", max_tokens=300)
        blocks = "\n".join(f"{b.start}-{b.end} {b.activity}" for b in p.blocks)
        s = self.llm.structured(self.system, f"Your plan for today:\n{blocks}\n\nTask: decompose the plan into "
                                "4 to 10 concrete steps, each with a start time (HH:MM, increasing) and a short "
                                "action.", Steps, tag="decompose", max_tokens=400)
        self.steps = s.steps
        self.pending.append(("plan", f"My plan for today: {blocks.replace(chr(10), '; ')}"))
        self.llm.run.log("plan", agent=self.persona.name, blocks=p.model_dump()["blocks"],
                         steps=s.model_dump()["steps"])
        return self.steps

    def act(self, step: Step, events: list[str]) -> Act:
        query = f"{step.action} " + " ".join(events)
        mems = self.mem.retrieve(query, self.now, self.k, self.memory_budget)
        happened = "\n".join(f"- {e}" for e in events) or "- nothing new"
        a = self.llm.structured(self.system, f"Relevant memories:\n{fmt(mems)}\n\nIt is {self.now:%H:%M}. "
                                f"Planned now: {step.action}\nWhat just happened:\n{happened}\n\nTask: say in one "
                                f"sentence what {self.persona.name} does now, whether it changes the plan, and why.",
                                Act, tag="act", max_tokens=200)
        self.pending.append(("action", a.action))
        self.llm.run.log("act", agent=self.persona.name, time=f"{self.now:%H:%M}", planned=step.action,
                         events=events, **a.model_dump())
        return a

    def reflect(self):
        """Scaled-down Park reflection: one call over the most recent memories -> up to 3 cited insights."""
        recent = self.mem.recent(900)
        ids = {m.id for m in recent}

        class CitedReflection(Reflection):
            @model_validator(mode="after")
            def _cited(self):
                bad = {e for i in self.insights for e in i.evidence} - ids
                if bad:
                    raise ValueError(f"evidence ids {sorted(bad)} are not in the listed memories")
                return self

        r = self.llm.structured(self.system, f"Recent memories:\n{fmt(sorted(recent, key=lambda m: m.id))}\n\n"
                                "Task: what 1 to 3 high-level insights about yourself or your situation follow from "
                                "these memories? Cite the memory ids in [brackets] as evidence.", CitedReflection,
                                tag="reflect", max_tokens=350)
        self.mem.importance_since_reflection = 0
        self.mem.add_many([("reflection", i.insight) for i in r.insights], self.now,
                          evidence=[i.evidence for i in r.insights], count_for_reflection=False)
        self.reflections += 1
        self.llm.run.log("reflection", agent=self.persona.name, insights=r.model_dump()["insights"])

    def interview(self, question: str) -> tuple[str, list[Memory]]:
        """A probe of memory (low temperature): first the ids of the memories that answer the question,
        then a short first-person answer. The interview itself is not stored."""
        mems = self.mem.retrieve(question, self.now, self.k, self.memory_budget)
        ids = {m.id for m in mems}

        class CitedAnswer(Answer):
            @model_validator(mode="after")
            def _cited(self):
                if bad := set(self.memories_used) - ids:
                    raise ValueError(f"memory ids {sorted(bad)} are not in the listed memories")
                return self

        a = self.llm.structured(self.system, f"Relevant memories:\n{fmt(mems)}\n\nInterviewer: {question}\n\nTask: "
                                "first list the ids of the memories that answer the question (an empty list if "
                                f"none do), then answer as {self.persona.name} in the first person in at most two "
                                "sentences, using only those memories. If none answer it, say you don't know.",
                                CitedAnswer, tag="interview", judge=True, max_tokens=200)
        self.llm.run.log("interview", agent=self.persona.name, question=question, answer=a.answer,
                         memories_used=a.memories_used, retrieved=[m.id for m in mems])
        return a.answer, mems

    def save(self, path: Path):
        path.write_text(json.dumps({"persona": self.persona.model_dump(), "now": self.now.isoformat(),
                                    "reflect_threshold": self.reflect_threshold, "reflections": self.reflections,
                                    "importance_since_reflection": self.mem.importance_since_reflection,
                                    "steps": [s.model_dump() for s in self.steps],
                                    "memories": [m.model_dump(mode="json") for m in self.mem.memories]}, indent=1),
                        encoding="utf-8")

    @classmethod
    def load(cls, path: Path, llm: LLM, weights: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> "GenerativeAgent":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        a = cls(Persona(**d["persona"]), llm, datetime.fromisoformat(d["now"]), d["reflect_threshold"],
                weights=weights)
        a.mem.memories = [Memory(**m) for m in d["memories"]]
        a.mem.importance_since_reflection = d["importance_since_reflection"]
        a.steps, a.reflections = [Step(**s) for s in d["steps"]], d["reflections"]
        return a


class Event(BaseModel):
    time: str = Field(pattern=HHMM)
    text: str


class Day(BaseModel):
    date: str
    wake: str = Field(pattern=HHMM)
    sleep: str = Field(pattern=HHMM)
    events: list[Event]

    @classmethod
    def from_yaml(cls, path):
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))


class Question(BaseModel):
    question: str
    expect: list[str]
    source: str


def recall_eval(agent: GenerativeAgent, questions: list[Question]) -> list[dict]:
    """Keyword check on answers, plus whether retrieval surfaced a memory with the keyword."""
    rows = []
    for q in questions:
        answer, mems = agent.interview(q.question)
        hit = lambda text: any(k.lower() in text.lower() for k in q.expect)  # noqa: E731
        rows.append({"question": q.question, "source": q.source, "answer": answer, "passed": hit(answer),
                     "retrieved_relevant": any(hit(m.text) for m in mems) if q.source != "none" else None})
    return rows


def run_day(agent: GenerativeAgent, day: Day) -> list[dict]:
    """Seed, plan, then walk the decomposed steps; scripted events arrive at their times."""
    agent.now = datetime.fromisoformat(f"{day.date}T{day.wake}")
    if not agent.mem.memories:
        agent.seed()
    agent.plan_day(day.wake, day.sleep)
    log, done = [], set()
    for step in agent.steps:
        agent.now = agent.at(step.time)
        events = [e.text for i, e in enumerate(day.events) if e.time <= step.time and i not in done]
        done |= {i for i, e in enumerate(day.events) if e.time <= step.time}
        for e in events:
            agent.observe(e)
        agent.commit()
        a = agent.act(step, events)
        log.append({"time": step.time, "planned": step.action, "events": events, **a.model_dump()})
    for i, e in enumerate(day.events):  # events after the last step still get observed
        if i not in done:
            agent.observe(e.text)
    agent.now = agent.at(day.sleep)
    agent.commit()
    return log
