import json
import re

import pytest

from agents_lab.simulation_multi.pipeline import (GameConfig, evaluate, comparison, condition_markdown,
                                                  promise_metrics, spread_metrics)
from agents_lab.simulation_multi.scenario import Bot, Contribution, PublicGoods

CFG = GameConfig(theme="garden fund", rounds=3, private_fact={"seat": 0, "text": "The council adds a grant.",
                                                               "keywords": ["council", "grant"]})


def test_public_goods_payoffs_and_metrics():
    g = PublicGoods(rounds=2, multiplier=1.5)
    assert g.payoffs({"a": 10, "b": 10, "c": 0}) == {"a": 10.0, "b": 10.0, "c": 20.0}  # pot 20 x 1.5 = 30, 10 each
    log = [{"outcome": g.apply(1, {k: Contribution(reason="r", contribution=v) for k, v in
                                  {"a": 10, "b": 4, "c": 1}.items()})},
           {"outcome": g.apply(2, {k: Contribution(reason="r", contribution=v) for k, v in
                                  {"a": 4, "b": 1, "c": 1}.items()})}]
    m = g.metrics(log)
    assert m["mean_contribution_by_round"] == [5.0, 2.0] and m["trend_per_round"] == pytest.approx(-3.0)
    assert m["total_payoffs"]["c"] == pytest.approx(10 - 1 + 7.5 + 10 - 1 + 3.0)


def test_bots():
    hist = [{"contributions": {"me": 10, "x": 2, "y": 5}}]
    assert Bot("me", "conditional").intended(2, hist) == 4  # round(3.5) -> 4 (banker's rounding gives 4)
    assert Bot("me", "conditional").intended(1, []) == 10
    assert Bot("me", "never").chat(1, []) == ("I will put 0 tokens into the pot this round.", 0)


def msg_log(rounds):
    """rounds: list of {name: message}; contributions all 5, promises 6 for 'a'."""
    return [{"round": i + 1, "messages": {n: {"message": m, "promise": 6 if n == "a" else -1} for n, m in r.items()},
             "outcome": {"contributions": {n: 5 for n in "abc"}}} for i, r in enumerate(rounds)]


def test_spread_and_promises():
    log = msg_log([{"a": "hi", "b": "the council grant?", "c": "ok"},   # b knows before a said it
                   {"a": "the council gives a grant", "b": "x", "c": "y"},
                   {"a": "go", "b": "y", "c": "grant!"}])
    s = spread_metrics(log, "a", ["council", "grant"])
    assert s["owner_first_mention"] == 2 and s["knowledge_before_exposure"] == ["b"] and s["spread_to"] == ["c"]
    p = promise_metrics(log)
    assert (p["promises"], p["kept"], p["broken"]) == (3, 0, 3) and p["mean_gap_contribution_minus_promise"] == -1


NAMES = ["Ana", "Ben", "Cara"]


def game_mock():
    def h(messages, schema):
        system, user = messages[0]["content"], messages[1]["content"]
        me = next((n for n in NAMES if f"You are {n}" in system), None)
        if schema == "Built":
            return json.dumps({"personas": [{"name": n, "age": 40, "background": "neighbour", "goal": "win",
                                             "private_info": "likes roses"} for n in NAMES], "world_state": "spring"})
        if schema == "Ratings":
            n = int(re.search(r"exactly (\d+) integers", user).group(1))
            return json.dumps({"ratings": [6] * n})
        if schema == "Strategy":
            return json.dumps({"plan": "cooperate"})
        if schema == "ChatOut":
            t = int(re.search(r"Task: round (\d+)", user).group(1))
            text = "The council will add a grant" if (me == "Ana" and t == 2) else f"I'll give 7, says {me}"
            return json.dumps({"message": text, "promise": 7})
        if schema == "Contribution":
            return json.dumps({"reason": "fair", "contribution": 7 if me != "Cara" else 3})
        if schema == "CitedReflection":
            ids = [int(x) for x in re.findall(r"^\[(\d+)\]", user, re.M)]
            return json.dumps({"insights": [{"insight": "people cooperate", "evidence": ids[:1]}]})
        if schema == "Misstatements":
            return json.dumps({"items": []})
        if schema == "ObserverReport":
            return json.dumps({k: "ok" for k in ["cooperation_trend", "private_fact_spread", "promises_vs_actions",
                                                 "hallucinated_knowledge", "summary"]})
        raise AssertionError(schema)
    return h


def test_full_eval_on_mock(make_llm):
    llm, backend = make_llm(game_mock())
    built, results = evaluate(CFG, llm, bots=[(2, "conditional")])
    assert "council" in built.personas[0].private_info  # private fact from config goes to seat 0
    chat, nochat, bot = results
    assert [r["outcome"]["contributions"] for r in chat["log"]][0] == {"Ana": 7, "Ben": 7, "Cara": 3}
    assert chat["metrics"]["promises"]["broken"] == 3  # Cara promised 7 and gave 3 every round
    assert chat["metrics"]["private_fact"]["owner_first_mention"] == 2
    assert not nochat["log"][0]["messages"]
    calls = [c["schema"] for c in backend.calls]
    assert calls.count("ChatOut") == 3 * 3 + 2 * 3  # chat run: 3 seats x 3 rounds; bot run: 2 LLM seats
    assert bot["log"][1]["outcome"]["contributions"]["Cara"] == 7  # conditional bot: mean of Ana 7, Ben 7
    # each persona has its own memory stream with the others' messages in it
    ben_prompts = [c["messages"][1]["content"] for c in backend.calls
                   if c["schema"] == "Ratings" and "memories of Ben" in c["messages"][1]["content"]]
    assert any("Ana said" in p for p in ben_prompts)
    assert "Observer" in condition_markdown(chat) and "bot_conditional@2" in comparison(results)


