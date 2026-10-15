import json
import re

import pandas as pd
import pytest

from agents_lab.decision_single.agent import DecisionAgent
from agents_lab.decision_single.compute import analyze, dominated, sensitivity
from agents_lab.decision_single.evaluate import evaluate, load_scenarios, report
from agents_lab.decision_single.schemas import Cell, Problem, score_schema


def cell(v, basis="fact", why="per F1"):
    return Cell(facts=[1], low=v, mid=v, high=v, justification=why, basis=basis)


def test_ev_ranking_and_closed_form_sensitivity():
    # X = (8, 4), Y = (4, 6), equal weights -> EV 6 vs 5, margin 1
    cells = {"X": {"a": cell(8), "b": cell(4)}, "Y": {"a": cell(4), "b": cell(6)}}
    a = analyze(cells, {"a": 1, "b": 1})
    assert a.ranking == ["X", "Y"] and a.margin == pytest.approx(1.0)
    w = a.sensitivity[a.sensitivity.change == "weight"].set_index("criterion")
    assert w.loc["a", "after"] == pytest.approx(1 / 3)  # check: (8+8)/3 == (4+12)/3 -> tie
    assert w.loc["b", "after"] == pytest.approx(2 / 3)
    s = a.sensitivity[a.sensitivity.change == "score"]
    assert set(s["size"].round(6)) == {2.0}  # margin / weight = 1 / 0.5


def test_pert_and_ranges():
    cells = {"X": {"a": Cell(facts=[1], low=2, mid=5, high=10, justification="F1", basis="fact")},
             "Y": {"a": cell(5)}}
    a = analyze(cells, {"a": 1})
    assert a.ev["X"] == pytest.approx((2 + 20 + 10) / 6)
    assert (a.ev_low["X"], a.ev_high["X"]) == (2, 10)
    assert a.ranking == ["X", "Y"]


def test_infeasible_flips_are_omitted():
    E = pd.DataFrame({"a": [10.0, 0.0], "b": [10.0, 0.0]}, index=["X", "Y"])
    s = sensitivity(E, pd.Series({"a": 0.5, "b": 0.5}), "X")
    # Y is worse everywhere: no weight flips it, and a score flip needs +-20, beyond the 0-10 scale
    assert s.empty


def test_dominated():
    E = pd.DataFrame({"a": [5, 6, 9], "b": [5, 5, 1]}, index=["A", "B", "C"], dtype=float)
    assert dominated(E) == ["A"]


def test_all_scenarios_load_with_valid_references():
    ps = load_scenarios()
    assert len(ps) >= 10
    cats = {p.reference.category for p in ps}
    assert cats == {"dominated", "clear", "close"}
    assert all("reference" not in p.prompt().lower() and p.reference.best not in p.prompt().split("Facts:")[0]
               .split("Options:")[0] for p in ps)


def test_score_schema_requires_real_fact_citation():
    p = load_scenarios(limit=1)[0]  # laptop: F1 Aero, F2 Bolt, F3 Core, F4 all three (no names)
    S = score_schema(p)
    assert set(S.model_json_schema()["properties"]) == set(p.options)  # keyed by option name
    good = {o: {"facts": p.facts_about(o), "low": 1, "mid": 2, "high": 3, "justification": "ok", "basis": "fact"}
            for o in p.options}
    S.model_validate(good)
    assert p.facts_about("Bolt 15") == [2, 4]
    for bad_ids in [[], [99], [1]]:  # F1 is about Aero 14, not Bolt 15
        bad = json.loads(json.dumps(good))
        bad["Bolt 15"]["facts"] = bad_ids
        with pytest.raises(ValueError):
            S.model_validate(bad)
    bad["Bolt 15"] |= {"facts": [], "basis": "assumption"}
    S.model_validate(bad)  # assumptions need no fact id


def mock_handler(values, bad_first=False):
    """values[option] -> mid score on every criterion; cites the facts the prompt lists for the option."""
    state = {"bad": bad_first}

    def h(messages, schema):
        user = messages[1]["content"]
        if schema == "Clarification":
            return json.dumps({"missing_info": ["delivery dates"], "assumptions": ["prices hold"]})
        if schema == "Scores":
            listed = dict(re.findall(r"([^;:]+): (F[\d, F]+)", user.split("Relevant facts per option: ")[1]
                                     .split(". For each")[0]))
            out = {}
            for opt, ids in listed.items():
                v, facts = values[opt.strip()], [int(x) for x in re.findall(r"\d+", ids)]
                if state.pop("bad", False):
                    facts = [99]
                out[opt.strip()] = {"facts": facts, "low": v - 1, "mid": v, "high": v + 1, "justification": "x",
                                    "basis": "fact"}
            return json.dumps(out)
        if schema == "Memo":
            return json.dumps({"rationale": "Best on F1.", "confidence": "medium", "key_risks": ["price"],
                               "evidence_that_would_change": ["new quote"]})
        raise AssertionError(schema)
    return h


def test_agent_loop_on_mock_shares_prompt_prefix(make_llm):
    p = load_scenarios(limit=1)[0]  # laptop
    values = {"Aero 14": 6, "Bolt 15": 3, "Core 13": 8}
    llm, backend = make_llm(mock_handler(values, bad_first=True))
    r = DecisionAgent(llm).run(p)
    assert r.recommendation == "Core 13" and r.analysis.dominated == ["Aero 14", "Bolt 15"]
    tags = [c["schema"] for c in backend.calls]
    assert tags == ["Clarification"] + ["Scores"] * 5 + ["Memo"]  # 4 criteria + one retry after fact 99
    prefix = p.prompt() + "\n\n" + r.clarification.context()
    assert all(c["messages"][1]["content"].startswith(prefix) for c in backend.calls[1:])
    assert all(c["options"]["temperature"] == 0.1 for c in backend.calls if c["schema"] == "Scores")
    md = r.to_markdown()
    assert "**Recommendation: Core 13**" in md and "Sensitivity" in md


def test_evaluate_and_report_on_mock(make_llm):
    ps = load_scenarios(limit=2)  # laptop (dominated), heating (close)
    vals = {"Aero 14": 6, "Bolt 15": 3, "Core 13": 8, "Heat pump": 7, "Gas boiler": 5, "Pellet stove": 6}
    llm, _ = make_llm(mock_handler(vals))
    df = evaluate(ps, llm, stability=1)
    assert len(df) == 4 and df.correct.all() and not df.dominated_recommended.any()
    text = report(df, llm)
    assert "Agreement with reference" in text and "Top-1 stable across seeds: 1 of 1" in text

