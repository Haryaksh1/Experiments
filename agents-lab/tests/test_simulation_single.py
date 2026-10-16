import json
import re
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from agents_lab.core.relevance import tfidf_relevance
from agents_lab.simulation_single.agent import (Day, GenerativeAgent, Persona, Question, Step, recall_eval,
                                                run_day)
from agents_lab.simulation_single.calibrate import calibrate
from agents_lab.simulation_single.memory import MemoryStream, minmax
from agents_lab.simulation_single.silicon import Instrument, Item, prepare_gss, run_survey, survey_schema

T0 = datetime(2026, 3, 14, 8, 0)


def ratings(user, value=5):
    n = int(re.search(r"exactly (\d+) integers", user).group(1))
    return json.dumps({"ratings": [value] * n})


def test_tfidf_relevance():
    r = tfidf_relevance("boiler broke hot water", ["the boiler broke", "went for a run", "bought bread"])
    assert r.argmax() == 0 and r[0] > 0 and r[1] == 0
    assert len(tfidf_relevance("x", [])) == 0
    assert (tfidf_relevance("the and of", ["the", "of"]) == 0).all()  # stop words only


def test_minmax_constant_is_ones():
    assert (minmax(np.array([3.0, 3.0])) == 1).all()
    assert list(minmax(np.array([1.0, 3.0, 2.0]))) == [0, 1, 0.5]


def test_add_many_is_one_call_and_retries_wrong_length(make_llm):
    llm, backend = make_llm(['{"ratings": [5]}', '{"ratings": [2, 9]}'])
    ms = MemoryStream(llm, "Maya")
    new = ms.add_many([("observation", "a"), ("observation", "b")], T0)
    assert [m.importance for m in new] == [2, 9] and len(backend.calls) == 2  # first reply had wrong length
    assert ms.importance_since_reflection == 11


def test_retrieval_score_components_and_budget(make_llm):
    llm, _ = make_llm(lambda m, s: ratings(m[1]["content"]))
    ms = MemoryStream(llm, "Maya")
    old, imp, rel = ms.add_many([("observation", "old memory"), ("observation", "important memory"),
                                 ("observation", "the boiler broke")], T0)
    old.last_access = T0 - timedelta(hours=200)  # recency 0.995**200 = 0.37
    imp.importance, rel.importance, old.importance = 10, 1, 1
    s = ms.scores("boiler", T0)
    assert s[old.id] == pytest.approx(0 + 0 + 0)          # oldest, least important, irrelevant
    assert s[imp.id] == pytest.approx(1 + 1 + 0)
    assert s[rel.id] == pytest.approx(1 + 0 + 1)
    assert [m.id for m in ms.retrieve("boiler", T0, k=2)] in ([imp.id, rel.id], [rel.id, imp.id])
    assert old.last_access == T0 - timedelta(hours=200) and rel.last_access == T0
    tiny = ms.retrieve("boiler", T0, k=3, token_budget=llm.estimate_tokens("the boiler broke"))
    assert len(tiny) == 1  # budget fits one memory; nothing is truncated


class Mock:
    """Schema-keyed mock for the generative agent."""

    def __init__(self, answer="I don't know."):
        self.answer = answer

    def __call__(self, messages, schema):
        user = messages[1]["content"]
        if schema == "Ratings":
            return ratings(user, 9)
        if schema == "DayPlan":
            return json.dumps({"blocks": [{"start": "07:00", "end": "10:00", "activity": "run"},
                                          {"start": "10:00", "end": "15:00", "activity": "chores"},
                                          {"start": "15:00", "end": "22:00", "activity": "relax"}]})
        if schema == "Steps":
            return json.dumps({"steps": [{"time": t, "action": f"do {t}"} for t in ["08:00", "10:00", "12:00", "16:00"]]})
        if schema == "Act":
            return json.dumps({"action": "keeps going", "changes_plan": False, "reason": "fine"})
        if schema == "CitedReflection":
            ids = [int(x) for x in re.findall(r"^\[(\d+)\]", user, re.M)]
            return json.dumps({"insights": [{"insight": "I am busy", "evidence": ids[:2]}]})
        if schema == "CitedAnswer":
            return json.dumps({"memories_used": [], "answer": self.answer})
        raise AssertionError(schema)


def make_agent(make_llm, threshold=150, answer="I don't know."):
    llm, backend = make_llm(Mock(answer))
    p = Persona(name="Maya", age=34, description="A nurse.", backstory=["I run.", "I have a brother."])
    return GenerativeAgent(p, llm, T0, reflect_threshold=threshold), backend


def test_run_day_events_arrive_before_acting_and_reflection_fires(make_llm, tmp_path):
    agent, backend = make_agent(make_llm, threshold=40)
    day = Day(date="2026-03-14", wake="07:00", sleep="22:00",
              events=[{"time": "09:00", "text": "boiler broke"}, {"time": "21:00", "text": "late call"}])
    log = run_day(agent, day)
    assert [r["events"] for r in log] == [[], ["boiler broke"], [], []]
    act_prompts = [c["messages"][1]["content"] for c in backend.calls if c["schema"] == "Act"]
    assert "boiler broke" in act_prompts[1]
    texts = [m.text for m in agent.mem.memories]
    assert "late call" in texts and texts.count("keeps going") == 4  # last action and late event stored at sleep
    assert agent.reflections >= 1 and any(m.kind == "reflection" and m.evidence for m in agent.mem.memories)
    agent.save(tmp_path / "a.json")
    back = GenerativeAgent.load(tmp_path / "a.json", agent.llm)
    assert len(back.mem.memories) == len(agent.mem.memories) and back.steps == agent.steps


def test_reflection_rejects_unlisted_evidence(make_llm):
    agent, backend = make_agent(make_llm)
    agent.seed()
    backend.script = [json.dumps({"insights": [{"insight": "x", "evidence": [999]}]}),
                      json.dumps({"insights": [{"insight": "x", "evidence": [0]}]}),
                      ratings("exactly 1 integers")]
    agent.reflect()
    assert backend.script == []  # rejected once, accepted on retry, then rated
    assert agent.mem.memories[-1].evidence == [0]


def test_recall_eval_keywords(make_llm):
    agent, _ = make_agent(make_llm, answer="Tunde got an internship at Siemens.")
    agent.seed()
    rows = recall_eval(agent, [Question(question="brother?", expect=["siemens"], source="event"),
                               Question(question="cousin?", expect=["don't know"], source="none")])
    assert rows[0]["passed"] and not rows[1]["passed"] and rows[1]["retrieved_relevant"] is None


INS = Instrument(items=[Item(id="cappun", question="Death penalty?", options=["Favor", "Oppose"], codes=[1, 0],
                             gss_labels=["favor", "oppose"]),
                        Item(id="happy", question="Happy?", options=["Very happy", "Pretty happy", "Not too happy"],
                             codes=[3, 2, 1], gss_labels=["very happy", "pretty happy", "not too happy"])])


def test_survey_schema_and_run(make_llm):
    assert survey_schema(INS).model_json_schema()["properties"]["cappun"]["enum"] == ["Favor", "Oppose"]

    def h(messages, schema):
        u = messages[1]["content"]
        assert u.startswith("Survey questions:")  # instrument first: shared prefix for the cache
        return json.dumps({"cappun": "Favor" if "republican" in u else "Oppose", "happy": "Pretty happy"})
    llm, _ = make_llm(h)
    personas = pd.DataFrame({"id": [1, 2], "party": ["strong republican", "strong democrat"]})
    sim = run_survey(personas, INS, llm)
    assert sim.to_dict("records") == [{"id": 1, "cappun": 1, "happy": 2}, {"id": 2, "cappun": 0, "happy": 2}]


def test_calibrate_synthetic_flattening():
    rng = np.random.default_rng(0)
    n_all = 400
    group = np.where(np.arange(n_all) % 2 == 0, "D", "R")
    real = rng.binomial(1, np.where(group == "R", 0.8, 0.4)).astype(float)
    sim = (group == "R").astype(float)  # perfectly party-determined: no within-group spread
    real_df = pd.DataFrame({"id": range(n_all), "group": group, "cappun": real})
    sim_df = pd.DataFrame({"id": range(n_all), "cappun": sim})
    est, spread = calibrate(real_df, sim_df, set(range(100)), ["cappun"])
    e = est.iloc[0]
    assert (e.n, e.N) == (100, 300) and e.ci_low < e.truth_all_real < e.ci_high
    assert e.n_eff > e.n and 0 < e.rho < 1
    within = spread[spread.group != "all"]
    assert (within.sd_ratio_sim_over_real == 0).all()  # flattened inside each party


def test_prepare_gss_from_synthetic_stata(tmp_path):
    k = 30
    cat = lambda vals: pd.Categorical([vals[i % len(vals)] for i in range(k)])  # noqa: E731
    df = pd.DataFrame({"id": np.arange(1, k + 1, dtype="int32"), "age": cat(["34", "56", "71"]),
                       "sex": cat(["male", "female"]), "race": cat(["white", "black"]),
                       "degree": cat(["bachelor's", "high school"]), "region": cat(["south atlantic"]),
                       "partyid": cat(["strong democrat", "not very strong republican", "independent"]),
                       "polviews": cat(["liberal", "conservative"]),
                       "cappun": cat(["favor", "oppose", "favor"]),
                       "happy": cat(["very happy", "pretty happy", "not too happy", "iap"])})
    path = tmp_path / "gss.dta"
    df.to_stata(path, write_index=False)
    personas, real, labeled = prepare_gss(path, INS, n=5, N=10)
    assert len(personas) == 15 and len(labeled) == 5 and set(labeled) <= set(personas.id)
    assert real.happy.notna().all()  # "iap" respondents were excluded from the pool
    assert set(real.group) <= {"Democrat", "Republican", "Independent/other"}
    assert "group" not in personas and "party identification" in personas
    assert set(personas.age) <= {"34", "56", "71"}

