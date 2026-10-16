from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field, create_model, model_validator

Line = Annotated[str, Field(max_length=160)]


class Criterion(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    weight: float = Field(gt=0)
    description: str  # states the direction, e.g. "lower price is better"


class Reference(BaseModel):
    best: str
    dominated: list[str] = []
    category: Literal["dominated", "clear", "close"]


class Problem(BaseModel):
    id: str
    question: str
    options: list[str] = Field(min_length=2)
    criteria: list[Criterion] = Field(min_length=1)
    facts: list[str] = Field(min_length=1)
    uncertainties: list[str] = []
    constraints: list[str] = []
    reference: Reference | None = None  # eval only; never shown to the model

    @model_validator(mode="after")
    def _check(self):
        names = [c.name for c in self.criteria]
        if len(set(self.options)) != len(self.options) or len(set(names)) != len(names):
            raise ValueError("option and criterion names must be unique")
        if self.reference and (bad := {self.reference.best, *self.reference.dominated} - set(self.options)):
            raise ValueError(f"reference names not in options: {bad}")
        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Problem":
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def facts_about(self, option: str) -> list[int]:
        """Fact ids (1-based) that mention `option` or mention no option at all."""
        def names(f):
            return [o for o in self.options if o.lower() in f.lower()]
        return [i for i, f in enumerate(self.facts, 1) if option in names(f) or not names(f)]

    @property
    def weights(self) -> dict[str, float]:
        return {c.name: c.weight for c in self.criteria}

    def prompt(self) -> str:
        """Problem text. Always the first thing in the user prompt, so Ollama's prefix cache reuses it."""
        parts = [f"Decision: {self.question}", "Options: " + "; ".join(self.options),
                 "Criteria (weight; 10 = best for the decision-maker):",
                 *[f"- {c.name} ({c.weight:g}): {c.description}" for c in self.criteria],
                 "Facts:", *[f"F{i}. {f}" for i, f in enumerate(self.facts, 1)]]
        if self.uncertainties:
            parts += ["Uncertainties:", *[f"- {u}" for u in self.uncertainties]]
        if self.constraints:
            parts += ["Constraints:", *[f"- {c}" for c in self.constraints]]
        return "\n".join(parts)


class Clarification(BaseModel):
    missing_info: list[Line] = Field(max_length=4)
    assumptions: list[Line] = Field(max_length=4)

    def context(self) -> str:
        return "\n".join(["Missing information:", *([f"- {m}" for m in self.missing_info] or ["- none"]),
                          "Assumptions:", *([f"A{i}. {a}" for i, a in enumerate(self.assumptions, 1)] or ["- none"])])


class Cell(BaseModel):
    facts: list[int] = Field(max_length=3)  # ids of the facts used; first, so evidence precedes the score
    low: int = Field(ge=0, le=10)
    mid: int = Field(ge=0, le=10)
    high: int = Field(ge=0, le=10)
    justification: str = Field(max_length=160)
    basis: Literal["fact", "assumption"]

    @model_validator(mode="after")
    def _order(self):
        if not self.low <= self.mid <= self.high:
            raise ValueError("need low <= mid <= high")
        return self


def cited_cell(problem: Problem, option: str) -> type[Cell]:
    """A cell with basis "fact" must cite facts about this option (see Problem.facts_about)."""
    allowed = problem.facts_about(option)
    ids_text = ", ".join(map(str, allowed))

    class CitedCell(Cell):
        @model_validator(mode="after")
        def _cites(self):
            if self.basis == "fact" and (not self.facts or not set(self.facts) <= set(allowed)):
                raise ValueError(f'basis "fact" needs facts about {option}: numbers from {ids_text}')
            return self

    return CitedCell


def score_schema(problem: Problem) -> type[BaseModel]:
    """Scores for ONE criterion across all options: one field per option (keyed by option name),
    so the grammar forces every option and the model compares them within a single call."""
    return create_model("Scores", **{f"o{i}": (cited_cell(problem, o), Field(alias=o))
                                     for i, o in enumerate(problem.options)})


class Memo(BaseModel):
    rationale: str = Field(max_length=500)
    confidence: Literal["low", "medium", "high"]
    key_risks: list[Line] = Field(min_length=1, max_length=3)
    evidence_that_would_change: list[Line] = Field(min_length=1, max_length=3)
