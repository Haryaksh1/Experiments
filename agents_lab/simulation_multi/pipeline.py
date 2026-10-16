"""Phase 4 pipeline: exactly three agent steps; only Step 2 is multi-agent.

Step 1 Scenario Builder (one agent): three personas + world state, schema-validated. The private fact
        whose spread we measure comes from config (with detection keywords), not from the model.
Step 2 Interaction (exactly three Phase 2 generative agents, each with its own memory stream):
        every round each sends one chat message, reads the others', then privately decides.
        Python applies the rules and payoffs. Baselines replace a seat with a fixed-strategy bot.
Step 3 Observer (one agent): Python computes every number; the Observer lists misstatements in the
        transcript and interprets the metrics.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from agents_lab.core.conversation import compress
from agents_lab.core.llm import LLM, BudgetExceeded
from agents_lab.core.trace import md_table
from agents_lab.simulation_multi.scenario import Bot, PublicGoods, Scenario
from agents_lab.simulation_single.agent import GenerativeAgent, Persona, fmt

BUILDER_SYSTEM = ("You are the Scenario Builder. You create believable characters and a starting situation for a "
                  "three-person simulation. Reply with JSON only.")
OBSERVER_SYSTEM = ("You are the Observer. You read a simulation log and the metrics computed from it, and you "
                   "interpret them faithfully without inventing numbers. Reply with JSON only.")


class PrivateFact(BaseModel):
    seat: int = Field(ge=0, le=2)
    text: str
    keywords: list[str] = Field(min_length=1)


class GameConfig(BaseModel):
    scenario: Literal["public_goods"] = "public_goods"
    theme: str
    rounds: int = 8
    endowment: int = 10
    multiplier: float = 1.5
    private_fact: PrivateFact
    reflect_threshold: int = 150

    @classmethod
    def from_yaml(cls, path):
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def make_scenario(self) -> Scenario:
        return PublicGoods(self.rounds, self.endowment, self.multiplier)


class PersonaSpec(BaseModel):
    name: str = Field(max_length=30)
    age: int = Field(ge=18, le=90)
    background: str = Field(max_length=160)
    goal: str = Field(max_length=120)
    private_info: str = Field(max_length=120)


class Built(BaseModel):
    personas: list[PersonaSpec] = Field(min_length=3, max_length=3)
    world_state: str = Field(max_length=300)

    @model_validator(mode="after")
    def _unique(self):
        names = [p.name.strip().lower() for p in self.personas]
        if len(set(names)) != 3 or any(not n for n in names):
            raise ValueError("the three personas need three different, non-empty names")
        return self


def build(cfg: GameConfig, scenario: Scenario, llm: LLM, seed: int | None = None) -> Built:
    b = llm.structured(BUILDER_SYSTEM, f"{scenario.rules()}\nSetting: {cfg.theme}\n\nTask: create exactly 3 "
                       "characters (different first names, age, a one-line background, their goal in this game, and "
                       "one private piece of information only they know) and a short initial world state.",
                       Built, tag="builder", seed=seed, max_tokens=600)
    k = cfg.private_fact.seat
    specs = list(b.personas)
    specs[k] = specs[k].model_copy(update={"private_info": f"{specs[k].private_info} {cfg.private_fact.text}"})
    b = Built.model_construct(personas=specs, world_state=b.world_state)
    llm.run.log("built", personas=[p.model_dump() for p in specs], world_state=b.world_state,
                private_fact_owner=specs[k].name)
    return b


class ChatOut(BaseModel):
    message: str = Field(max_length=160)
    promise: Literal[tuple(range(-1, 11))]  # tokens the message commits to; -1 = no commitment


class Strategy(BaseModel):
    plan: str = Field(max_length=200)


class PersonaSeat:
    """A Phase 2 generative agent in a seat: own system prompt, own memory stream, own plan."""
    is_llm = True

    def __init__(self, spec: PersonaSpec, built: Built, scenario: Scenario, llm: LLM, start: datetime,
                 seed: int, reflect_threshold: int):
        self.name, self.scenario, self.llm, self.start, self.seed = spec.name, scenario, llm, start, seed
        persona = Persona(name=spec.name, age=spec.age,
                          description=f"{spec.background} Your goal: {spec.goal} You privately know: {spec.private_info}",
                          backstory=[spec.background, f"My goal in the game: {spec.goal}",
                                     f"Private, only I know this: {spec.private_info}", f"Situation: {built.world_state}"])
        self.agent = GenerativeAgent(persona, llm, start, reflect_threshold=reflect_threshold, k=6, memory_budget=450)

    def begin(self):
        """Seed memories and make one strategy plan for the game (stored as a plan memory)."""
        self.agent.seed()
        mems = self.agent.mem.retrieve(f"{self.name} goal strategy game", self.start, 6, 450)
        s = self.llm.structured(self.agent.system, f"{self.scenario.rules()}\n\nRelevant memories:\n{fmt(mems)}\n\n"
                                "Task: in one or two sentences, what is your strategy for this game?", Strategy,
                                tag="plan", seed=self.seed, max_tokens=120)
        self.agent.pending.append(("plan", f"My strategy for the game: {s.plan}"))

    def observe(self, text: str):
        self.agent.observe(text)

    def _now(self, t: int):
        self.agent.now = self.start + timedelta(hours=t)

    def chat(self, t: int, history: list[dict]) -> tuple[str, int]:
        self._now(t)
        last = self.scenario.outcome_text(t - 1, history[-1]) if history else "This is the first round."
        mems = self.agent.mem.retrieve(f"round {t} chat promises contributions pot {last}", self.agent.now, 6, 450)
        out = self.llm.structured(self.agent.system, f"{self.scenario.rules()}\n\nRelevant memories:\n{fmt(mems)}\n\n"
                                  f"Last round: {last}\n\nTask: round {t}. Write one short chat message (under 30 "
                                  "words) to the other two players before anyone chooses. Then give promise: the "
                                  "number of tokens your message commits you to put in, or -1 if it commits to none.",
                                  ChatOut, tag="chat", seed=self.seed + t, max_tokens=150)
        self.agent.pending.append(("action", f"Round {t}: I said to the others: {out.message}"))
        return out.message, int(out.promise)

    def decide(self, t: int, history: list[dict], messages: dict[str, tuple[str, int]]):
        self._now(t)
        self.agent.commit()  # one importance call: last outcome, my last decision, this round's chat
        chat = "\n".join(f"- {n}: {m}" for n, (m, _) in messages.items()) or "- (no chat this round)"
        mems = self.agent.mem.retrieve(f"round {t} contributions promises pot {chat}", self.agent.now, 6, 450)
        d = self.llm.structured(self.agent.system, f"{self.scenario.rules()}\n\nRelevant memories:\n{fmt(mems)}\n\n"
                                f"This round's chat:\n{chat}\n\n{self.scenario.decision_task(t)}",
                                self.scenario.decision_schema(), tag="decide", seed=self.seed + 100 + t, max_tokens=120)
        self.agent.pending.append(("action", f"Round {t}: I put {d.contribution} tokens in. My reason: {d.reason}"))
        return d


class BotSeat(Bot):
    def begin(self):
        pass

    def observe(self, text: str):
        pass

    def decide(self, t, history, messages=None):
        return super().decide(t, history)


def run_interaction(seats: list, scenario: Scenario, llm: LLM, chat: bool = True) -> list[dict]:
    """Step 2. Messages are simultaneous (each seat sees only earlier rounds), then read, then decisions."""
    assert len(seats) == 3
    for s in seats:
        s.begin()
    history, log = [], []
    for t in range(1, scenario.rounds + 1):
        messages = {s.name: s.chat(t, history) for s in seats} if chat else {}
        for s in seats:
            for other, (m, _) in messages.items():
                if other != s.name:
                    s.observe(f"Round {t} chat: {other} said: {m}")
        decisions = {s.name: s.decide(t, history, messages) for s in seats}
        outcome = scenario.apply(t, decisions)
        history.append(outcome)
        for s in seats:
            s.observe(scenario.outcome_text(t, outcome))
        rec = {"round": t, "messages": {n: {"message": m, "promise": p} for n, (m, p) in messages.items()},
               "reasons": {n: d.reason for n, d in decisions.items()}, "outcome": outcome}
        log.append(rec)
        llm.run.log("round", **rec)
    for s in seats:
        if s.is_llm:
            s.agent.commit()
            llm.run.log("agent_state", agent=s.name, memories=len(s.agent.mem.memories),
                        reflections=s.agent.reflections)
    return log


def spread_metrics(log: list[dict], owner: str, keywords: list[str]) -> dict:
    """When the private fact first appears in the owner's and others' messages. Another seat mentioning
    it no later than the owner (messages are simultaneous) claims knowledge not in its memory."""
    def first(name):
        return next((r["round"] for r in log if name in r["messages"] and
                     any(k.lower() in r["messages"][name]["message"].lower() for k in keywords)), None)
    names = list(log[0]["outcome"]["contributions"])
    owner_first = first(owner)
    others = {n: first(n) for n in names if n != owner}
    leaked = [n for n, r in others.items() if r is not None and (owner_first is None or r <= owner_first)]
    return {"owner": owner, "owner_first_mention": owner_first, "others_first_mention": others,
            "spread_to": [n for n, r in others.items() if r is not None and n not in leaked],
            "knowledge_before_exposure": leaked}


def promise_metrics(log: list[dict]) -> dict:
    rows = [(r["round"], n, m["promise"], r["outcome"]["contributions"][n])
            for r in log for n, m in r["messages"].items() if m["promise"] >= 0]
    kept = [c >= p for _, _, p, c in rows]
    return {"promises": len(rows), "kept": sum(kept), "broken": len(rows) - sum(kept),
            "kept_rate": round(sum(kept) / len(rows), 3) if rows else None,
            "mean_gap_contribution_minus_promise": round(sum(c - p for *_, p, c in rows) / len(rows), 2) if rows else None,
            "broken_list": [f"R{t} {n}: promised {p}, gave {c}" for t, n, p, c in rows if c < p]}


def transcript(log: list[dict]) -> str:
    lines = []
    for r in log:
        for n, m in r["messages"].items():
            lines.append(f"R{r['round']} {n}: {m['message']}")
        lines.append("R{} result: ".format(r["round"]) + ", ".join(f"{n} gave {c}" for n, c in
                                                                   r["outcome"]["contributions"].items()))
    return "\n".join(lines)


class Misstatement(BaseModel):
    round: int
    agent: str
    statement: str = Field(max_length=150)
    why: str = Field(max_length=150)


class Misstatements(BaseModel):
    items: list[Misstatement] = Field(max_length=5)


class ObserverReport(BaseModel):
    cooperation_trend: str = Field(max_length=300)
    private_fact_spread: str = Field(max_length=300)
    promises_vs_actions: str = Field(max_length=300)
    hallucinated_knowledge: str = Field(max_length=300)
    summary: str = Field(max_length=300)


def observe(log: list[dict], metrics: dict, llm: LLM, names: list[str], fact: str, owner: str,
            chat: bool, seed: int | None = None) -> tuple[list[Misstatement], ObserverReport]:
    """Step 3: one agent, two calls (misstatements, then interpretation of the Python metrics)."""
    items = []
    if chat:
        class Checked(Misstatements):
            model_config = ConfigDict(title="Misstatements")

            class Item(Misstatement):
                round: Literal[tuple(range(1, len(log) + 1))]
                agent: Literal[tuple(names)]
            items: list[Item] = Field(max_length=5)

        text = transcript(log)
        task = (f"\n\nOnly {owner} privately knew: {fact}\nTask: list up to 5 chat statements that claim something "
                "the speaker could not know from earlier rounds' results, the chat so far, or their own private "
                "information (for example a wrong number for someone's past contribution, or the private fact "
                "before it was shared). Only list statements that assert something false or unknowable, not "
                "statements that merely leave something out. Use an empty list if there are none.")
        try:
            r = llm.structured(OBSERVER_SYSTEM, f"Simulation log:\n{text}{task}", Checked, tag="observer", judge=True,
                               seed=seed, max_tokens=450)
        except BudgetExceeded:  # older rounds compressed, the last three kept verbatim (logged)
            cut = "\n".join(l for l in text.splitlines() if int(l[1:].split()[0]) > len(log) - 3)
            older = compress(llm, "\n".join(l for l in text.splitlines() if int(l[1:].split()[0]) <= len(log) - 3))
            r = llm.structured(OBSERVER_SYSTEM, f"Simulation log (older rounds summarized):\n{older}\n{cut}{task}",
                               Checked, tag="observer", judge=True, seed=seed, max_tokens=450)
        items = r.items
    listed = "\n".join(f"- R{i.round} {i.agent}: {i.statement} ({i.why})" for i in items) or "- none listed"
    rep = llm.structured(OBSERVER_SYSTEM, f"Metrics computed in Python:\n{json.dumps(metrics, indent=1, default=float)}\n"
                         f"Statements the transcript check listed:\n{listed}\n\nTask: interpret these results: the "
                         "cooperation trend, whether and when the private fact spread, promises versus actual "
                         "contributions, and hallucinated knowledge; then a two-sentence summary. Use only the numbers "
                         "given; name who broke a promise only from broken_list.", ObserverReport, tag="observer_report", judge=True, seed=seed, max_tokens=500)
    llm.run.log("observer", misstatements=[i.model_dump() for i in items], report=rep.model_dump())
    return items, rep


def run_condition(cfg: GameConfig, built: Built, llm: LLM, chat: bool = True, bot: tuple[int, str] | None = None,
                  label: str = "") -> dict:
    scenario = cfg.make_scenario()
    start = datetime(2026, 1, 1, 9, 0)
    seats = []
    for i, spec in enumerate(built.personas):
        if bot and bot[0] == i:
            seats.append(BotSeat(spec.name, bot[1]))
        else:
            seats.append(PersonaSeat(spec, built, scenario, llm, start, (llm.cfg.seed + 1) * 1000 * (i + 1),
                                     cfg.reflect_threshold))
    llm.run.log("condition_start", label=label, chat=chat, bot=bot)
    log = run_interaction(seats, scenario, llm, chat=chat)                                      # Step 2
    owner = built.personas[cfg.private_fact.seat].name
    metrics = {**scenario.metrics(log), "private_fact": spread_metrics(log, owner, cfg.private_fact.keywords),
               "promises": promise_metrics(log)}
    names = [s.name for s in seats]
    items, rep = observe(log, metrics, llm, names, cfg.private_fact.text, owner, chat)          # Step 3
    return {"label": label, "chat": chat, "bot": bot, "log": log, "metrics": metrics, "misstatements": items,
            "report": rep, "reflections": {s.name: s.agent.reflections for s in seats if s.is_llm}}


def condition_markdown(r: dict) -> str:
    m, log = r["metrics"], r["log"]
    names = list(log[0]["outcome"]["contributions"])
    rows = [{"round": x["round"], **{n: x["outcome"]["contributions"][n] for n in names},
             **{f"{n} promise": x["messages"].get(n, {}).get("promise", "") for n in names}} for x in log]
    out = [f"## Condition: {r['label']} (chat {'on' if r['chat'] else 'off'}"
           + (f", bot '{r['bot'][1]}' in seat {r['bot'][0]}" if r["bot"] else "") + ")", "",
           md_table(pd.DataFrame(rows)), "",
           f"- mean contribution {m['mean_contribution']}, trend {m['trend_per_round']} per round, "
           f"first {m['first_round_mean']:.2f} -> last {m['last_round_mean']:.2f}",
           f"- total payoffs: {m['total_payoffs']}",
           f"- private fact: {m['private_fact']}",
           f"- promises: {m['promises']}",
           f"- reflections: {r['reflections']}",
           f"- misstatements listed by the Observer: {[i.model_dump() for i in r['misstatements']]}", "",
           "**Observer:**", "", *[f"- {k}: {v}" for k, v in r["report"].model_dump().items()], ""]
    if r["chat"]:
        out += ["<details><summary>Transcript</summary>", "", "```", transcript(log), "```", "</details>", ""]
    return "\n".join(out)


def evaluate(cfg: GameConfig, llm: LLM, bots: list[tuple[int, str]]) -> tuple[Built, list[dict]]:
    """Builder once (same personas everywhere), then: chat, no chat, and each bot substitution."""
    built = build(cfg, cfg.make_scenario(), llm, llm.cfg.seed)                                # Step 1
    conds = [("chat", True, None), ("no_chat", False, None)] + [(f"bot_{k}@{s}", True, (s, k)) for s, k in bots]
    return built, [run_condition(cfg, built, llm, chat, bot, label) for label, chat, bot in conds]


def comparison(results: list[dict]) -> str:
    rows = [{"condition": r["label"], "mean_contribution": r["metrics"]["mean_contribution"],
             "trend": r["metrics"]["trend_per_round"], "first": r["metrics"]["first_round_mean"],
             "last": r["metrics"]["last_round_mean"],
             "fact_spread_to": ", ".join(r["metrics"]["private_fact"]["spread_to"]) or "-",
             "knowledge_before_exposure": ", ".join(r["metrics"]["private_fact"]["knowledge_before_exposure"]) or "-",
             "promises_kept": f"{r['metrics']['promises']['kept']}/{r['metrics']['promises']['promises']}",
             "misstatements": len(r["misstatements"])} for r in results]
    return md_table(pd.DataFrame(rows))


