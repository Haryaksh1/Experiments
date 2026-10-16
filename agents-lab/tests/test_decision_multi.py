import json
import re

import pytest

from agents_lab.core.conversation import Turn
from agents_lab.decision_multi.ablations import claim_stats, conformity, evaluate, report
from agents_lab.decision_multi.deliberation import DebateTurn, turn_schema
from agents_lab.decision_multi.pipeline import run_pipeline
from agents_lab.decision_single.evaluate import load_scenarios
from test_decision_single import mock_handler

P = load_scenarios(limit=1)[0]  # laptop: reference Core 13
VALUES = {"Aero 14": 6, "Bolt 15": 3, "Core 13": 8}


def section(user, start, end):
    return user.split(start, 1)[1].split(end, 1)[0] if start in user else ""


def multi_mock(p=P):
    phase1 = mock_handler(VALUES)

    def h(messages, schema):
        system, user = messages[0]["content"], messages[1]["content"]
        if schema == "Brief":
            return json.dumps({"option_summaries": [{"option": o, "summary": "ok"}
                                                    for o in p.options],
                               "assumptions": ["prices hold"], "open_questions": ["keyboard?"]})
        if schema in ("DebateTurn", "AnalystTurn"):
            others = section(user, "Others' latest turns:", "Your previous turn:")
            ids = re.findall(r"\b(?:ADV|SKE|ANA)\d+\.\d+\b", others)
            first = "Task: state your position independently" in user
            skeptic = "Skeptic" in system
            # the Skeptic starts on the reference and abandons it once it has seen the others
            pref = "Aero 14" if skeptic and not first and ids else "Core 13"
            turn = {"preferred_option": pref, "position": "p",
                    "claims": [{"text": "claim", "facts": [] if skeptic else [3]}],
                    "accepts": [{"claim": ids[0], "reason": "r"}] if ids else [], "rejects": []}
            if schema == "AnalystTurn":
                ske = [i for i in ids if i.startswith("SKE")]
                turn["flags"] = [{"claim": ske[0], "reason": "no fact"}] if ske else []
            return json.dumps(turn)
        if schema == "JudgeScores":
            out = json.loads(phase1(messages, "Scores"))
            out["cited_claims"] = re.findall(r"\b(?:ADV|SKE|ANA)\d+\.\d+\b", user)[:1]
            return json.dumps(out)
        return phase1(messages, schema)
    return h


def test_turn_schema_validates_ids_facts_and_flags():
    plain = turn_schema(P, analyst=False, valid_ids={"SKE0.1"})
    assert "flags" not in plain.model_json_schema()["properties"]
    assert turn_schema(P, analyst=True, valid_ids=set()).model_json_schema()["title"] == "AnalystTurn"
    good = {"preferred_option": "Core 13", "position": "p", "claims": [{"text": "c", "facts": [3]}],
            "accepts": [{"claim": "SKE0.1", "reason": "r"}], "rejects": []}
    plain.model_validate(good)
    for bad in [{"accepts": [{"claim": "ANA0.1", "reason": "r"}]}, {"claims": [{"text": "c", "facts": [9]}]},
                {"preferred_option": "Mac"}]:
        with pytest.raises(ValueError):
            plain.model_validate(good | bad)


def test_pipeline_three_agents_conversing_and_judge_cites(make_llm):
    llm, backend = make_llm(multi_mock())
    r = run_pipeline(P, llm, rounds=2)
    assert {t.agent for t in r.turns} == {"Advocate", "Skeptic", "Analyst"} and len(r.turns) == 9
    assert sorted({t.round for t in r.turns}) == [0, 1, 2]
    systems = {c["messages"][0]["content"] for c in backend.calls if c["schema"] in ("DebateTurn", "AnalystTurn")}
    assert len(systems) == 3  # each agent has its own system prompt
    adv = [c["messages"][1]["content"] for c in backend.calls
           if c["schema"] == "DebateTurn" and "Advocate" in c["messages"][0]["content"]]
    assert "SKE0.1" in section(adv[1], "Others' latest turns:", "Your previous turn:")
    assert r.recommendation == "Core 13" and any(r.cited.values())
    assert any(getattr(t.content, "flags", []) for t in r.turns if t.agent == "Analyst")
    assert "Step 2: deliberation" in r.to_markdown()


def test_isolated_agents_never_see_each_other(make_llm):
    llm, backend = make_llm(multi_mock())
    r = run_pipeline(P, llm, rounds=2, visible=False)
    for c in backend.calls:
        if c["schema"] in ("DebateTurn", "AnalystTurn"):
            mine = {"Advocate": "ADV", "Skeptic": "SKE", "Analyst": "ANA"}
            me = next(v for k, v in mine.items() if k in c["messages"][0]["content"])
            seen = set(re.findall(r"\b(ADV|SKE|ANA)\d+\.\d+\b", c["messages"][1]["content"]))
            assert seen <= {me}
    assert not any(getattr(t.content, "flags", []) for t in r.turns)


def test_conformity_and_claim_stats():
    def t(agent, rnd, pref, facts=(1,)):
        return Turn(agent, rnd, DebateTurn(preferred_option=pref, position="p",
                                           claims=[{"text": "c", "facts": list(facts)}], accepts=[], rejects=[]))
    turns = [t("Skeptic", 0, "X"), t("Skeptic", 1, "Y", ()), t("Skeptic", 2, "X"),
             t("Advocate", 0, "Y"), t("Advocate", 1, "X")]
    assert conformity(turns, "X") == (1, 1)  # Skeptic left X once; Advocate never held X before
    assert claim_stats(turns)["no_fact_claims"] == 1


def test_ensemble_drops_failed_samples(make_llm):
    from agents_lab.decision_multi.ablations import run_ensemble

    good = multi_mock()
    state = {"bad_scores": 3}  # first sample's first criterion fails 3 times -> sample dropped

    def h(messages, schema):
        if schema == "Scores" and state["bad_scores"]:
            state["bad_scores"] -= 1
            return "{}"
        return good(messages, schema)
    llm, _ = make_llm(h)
    a, recs = run_ensemble(P, llm, k=2, seed=0)
    assert len(recs) == 1 and a.ranking[0] == "Core 13"
    assert any(e["event"] == "ensemble_sample_failed" for e in llm.run.events)


def test_ablation_eval_on_mock(make_llm):
    llm, _ = make_llm(multi_mock())
    df = evaluate([P], llm, rounds=1)
    assert list(df.condition) == ["A", "C", "B", "D"] and df.error.isna().all()
    b = df[df.condition == "B"].iloc[0]
    assert b.k >= 1 and len(b.sample_recommendations.split(", ")) == b.k
    c = df[df.condition == "C"].iloc[0]
    assert c.conformity_events == 1 and c.analyst_flags >= 1 and c.flags_on_no_fact >= 1
    text = report(df, llm)
    assert "Phase 3 ablations" in text and "not measured (1 seed)" in text

