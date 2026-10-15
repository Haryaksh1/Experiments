"""Phase 2 silicon-sample mode: many independent personas answer a survey.

This is still SINGLE-agent: every persona is a separate call that never sees any other persona.
Personas are a profile line built from attributes (or a `backstory` column), not memory streams.
"""
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import yaml
from pydantic import BaseModel, create_model, model_validator

from agents_lab.core.llm import LLM, LLMFailed

SYSTEM = ("You answer a public opinion survey as the person described, the way that person would really answer, "
          "not as an AI assistant. Reply with JSON only.")


class Item(BaseModel):
    id: str
    question: str
    options: list[str]
    codes: list[float]
    gss_labels: list[str] = []  # value labels in the GSS file, aligned with options

    @model_validator(mode="after")
    def _aligned(self):
        if len(self.codes) != len(self.options) or (self.gss_labels and len(self.gss_labels) != len(self.options)):
            raise ValueError(f"{self.id}: options, codes and gss_labels must align")
        return self


class Instrument(BaseModel):
    items: list[Item]

    @classmethod
    def from_yaml(cls, path):
        return cls(**yaml.safe_load(Path(path).read_text(encoding="utf-8")))

    def text(self) -> str:
        return "\n".join(f"{it.id}: {it.question} Options: " + " / ".join(it.options) for it in self.items)


def survey_schema(ins: Instrument) -> type[BaseModel]:
    return create_model("Survey", **{it.id: (Literal[tuple(it.options)], ...) for it in ins.items})


def profile(attrs: dict) -> str:
    if "backstory" in attrs:
        return str(attrs["backstory"])
    return "; ".join(f"{k}: {v}" for k, v in attrs.items() if pd.notna(v))


def run_survey(personas: pd.DataFrame, ins: Instrument, llm: LLM, id_col: str = "id") -> pd.DataFrame:
    """One call per persona. Instrument text goes first so Ollama's prefix cache reuses it."""
    schema, questions = survey_schema(ins), ins.text()
    rows = []
    for i, attrs in enumerate(personas.to_dict("records")):
        pid = attrs.pop(id_col)
        user = (f"Survey questions:\n{questions}\n\nRespondent: {profile(attrs)}\n\nTask: give this respondent's "
                "answer to every question, using the exact option text.")
        try:
            out = llm.structured(SYSTEM, user, schema, tag="survey", seed=llm.cfg.seed + i, max_tokens=150)
        except LLMFailed:
            rows.append({id_col: pid})
            continue
        rows.append({id_col: pid, **{it.id: it.codes[it.options.index(getattr(out, it.id))] for it in ins.items}})
    return pd.DataFrame(rows).reindex(columns=[id_col] + [it.id for it in ins.items])


# --- GSS preparation -------------------------------------------------------------------------------

PERSONA_COLS = {"age": "age", "sex": "sex", "race": "race", "degree": "highest degree", "region": "region",
                "partyid": "party identification", "polviews": "political views"}


def party_group(label: str) -> str:
    label = str(label).lower()
    return "Democrat" if "democrat" in label else "Republican" if "republican" in label else "Independent/other"


def prepare_gss(dta: Path, ins: Instrument, n: int, N: int, seed: int = 0):
    """-> personas (id + profile attributes), real answers (id, group, item codes), labeled ids.

    Samples respondents with complete demographics who answered every item; the first n are the
    'human sample' (real answers used), the other N are simulated-only (real answers held out as truth).
    """
    cols = ["id"] + list(PERSONA_COLS) + [it.id for it in ins.items]
    df = pd.read_stata(dta, columns=cols, convert_categoricals=True)
    real = pd.DataFrame({"id": df["id"].astype(int), "group": df["partyid"].map(party_group)})
    for it in ins.items:
        lookup = {lab.lower(): c for lab, c in zip(it.gss_labels, it.codes)}
        real[it.id] = df[it.id].astype(str).str.lower().map(lookup)
    complete = df[list(PERSONA_COLS)].notna().all(axis=1) & real[[it.id for it in ins.items]].notna().all(axis=1)
    pool = np.flatnonzero(complete.to_numpy())
    if len(pool) < n + N:
        raise ValueError(f"only {len(pool)} complete respondents, need {n + N}")
    pick = np.random.default_rng(seed).choice(pool, n + N, replace=False)
    sel = df.iloc[pick][["id"] + list(PERSONA_COLS)].copy()
    num = pd.to_numeric(sel["age"].astype(str), errors="coerce")  # "32" not "32.0"; labels like "89 or older" kept
    sel["age"] = [str(int(v)) if pd.notna(v) else str(a) for v, a in zip(num, sel["age"])]
    personas = sel.rename(columns=PERSONA_COLS).astype(str)
    personas["id"] = df["id"].iloc[pick].astype(int).to_numpy()
    return personas.reset_index(drop=True), real.iloc[pick].reset_index(drop=True), set(personas["id"][:n])
