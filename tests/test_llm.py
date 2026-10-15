import json

import pytest
from pydantic import BaseModel, Field

from agents_lab.core.config import load_config
from agents_lab.core.llm import BudgetExceeded, LLMFailed


class Pick(BaseModel):
    option: str
    score: int = Field(ge=0, le=10)


GOOD = '{"option": "A", "score": 7}'


def calls(llm):
    return [e for e in llm.run.events if e["event"] == "llm_call"]


def test_valid_first_try(make_llm):
    llm, backend = make_llm([GOOD])
    assert llm.structured("sys", "user", Pick, tag="t") == Pick(option="A", score=7)
    opts = backend.calls[0]["options"]
    assert opts["num_ctx"] == 4096 and opts["temperature"] == 0.7 and opts["num_thread"] == 4
    assert backend.calls[0]["schema"] == "Pick"
    assert len(calls(llm)) == 1


def test_repair_after_bad_json_and_out_of_range(make_llm):
    llm, backend = make_llm(['{"option": "A", "sco', '{"option": "A", "score": 42}', GOOD])
    assert llm.structured("sys", "user", Pick, tag="t").score == 7
    assert [c["options"]["seed"] for c in backend.calls] == [0, 1, 2]  # new seed per retry
    retry_prompt = backend.calls[2]["messages"][1]["content"]
    assert "score" in retry_prompt and "invalid" in retry_prompt
    s = llm.run.stats().iloc[0]
    assert (s.calls, s.attempts, s.failed_attempts, s.final_failures) == (1, 3, 2, 0)


def test_fails_loudly_after_two_retries(make_llm):
    llm, backend = make_llm(["nope"] * 3)
    with pytest.raises(LLMFailed):
        llm.structured("sys", "user", Pick, tag="t")
    assert len(backend.calls) == 3
    assert llm.run.stats().iloc[0].parse_fail_rate == 1.0
    assert llm.run.events[-1]["event"] == "llm_failed"


def test_judge_uses_low_temperature(make_llm):
    llm, backend = make_llm([GOOD])
    llm.structured("sys", "user", Pick, tag="t", judge=True)
    assert backend.calls[0]["options"]["temperature"] == 0.1


def test_budget_exceeded_before_calling(make_llm):
    llm, backend = make_llm([GOOD])
    with pytest.raises(BudgetExceeded):
        llm.structured("sys", "x" * 20_000, Pick, tag="t")
    assert backend.calls == []
    assert llm.run.events[-1]["event"] == "budget_exceeded"


def test_trace_and_summary(make_llm):
    llm, _ = make_llm([GOOD])
    llm.structured("sys", "user", Pick, tag="t")
    lines = [json.loads(l) for l in llm.run.path.read_text(encoding="utf-8").splitlines()]
    assert lines[0]["event"] == "run_start" and lines[0]["config"]["model"] == "phi3:mini" and "git" in lines[0]
    call = lines[-1]
    assert {"system", "user", "output", "prompt_tokens", "completion_tokens", "latency_s", "est_tokens"} <= call.keys()
    summary = llm.run.write_summary("hello").read_text(encoding="utf-8")
    assert "parse failure rate: 0.0%" in summary and "hello" in summary


def test_config_overrides(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("model: other\nnum_ctx: 2048\n")
    c = load_config(str(p), seed=5, temperature=None)
    assert (c.model, c.num_ctx, c.seed, c.temperature) == ("other", 2048, 5, 0.7)
