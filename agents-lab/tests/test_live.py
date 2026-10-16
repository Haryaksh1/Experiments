import pytest
from pydantic import BaseModel, Field

from agents_lab.core.config import load_config
from agents_lab.core.llm import LLM, OllamaBackend
from agents_lab.core.trace import Run


class Reason(BaseModel):
    claim: str = Field(max_length=120)
    support: str = Field(max_length=120)


class Answer(BaseModel):
    choice: str
    confidence: int = Field(ge=1, le=10)
    reasons: list[Reason] = Field(min_length=1, max_length=3)


@pytest.mark.live
def test_nested_schema_live(tmp_path):
    cfg = load_config()
    llm = LLM(OllamaBackend(cfg), cfg, Run("live", cfg, root=tmp_path))
    a = llm.structured("Pick the cheaper option.", "Option A costs $5. Option B costs $9.", Answer, tag="live",
                       judge=True, max_tokens=200)
    assert a.choice.strip().upper().startswith(("A", "OPTION A"))


@pytest.mark.live
def test_time_pattern_schema_live(tmp_path):
    """Regex patterns in schemas become grammars; an unsupported one crashes Ollama's runner."""
    from agents_lab.simulation_single.agent import DayPlan

    cfg = load_config()
    llm = LLM(OllamaBackend(cfg), cfg, Run("live", cfg, root=tmp_path))
    p = llm.structured("Plan a day.", "Make a plan from 07:00 to 22:00 in 3 to 5 blocks.", DayPlan, tag="live",
                       max_tokens=300)
    assert 3 <= len(p.blocks) <= 5


def test_no_backslash_d_in_schema_patterns():
    """Offline guard for the same crash: no \\d in any pattern used with format=."""
    import json

    from agents_lab.simulation_single.agent import DayPlan, Steps

    for schema in (DayPlan, Steps):
        assert "\\d" not in json.dumps(schema.model_json_schema())
