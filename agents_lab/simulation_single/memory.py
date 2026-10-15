"""Memory stream after Park et al. (UIST 2023), scaled down for a 4k context.

score = w_rec * minmax(recency) + w_imp * minmax(importance) + w_rel * minmax(relevance)
recency = 0.995 ** (simulated hours since last access); importance 1-10 rated by the model at
creation (one batched call per step); relevance = TF-IDF cosine (pluggable).
"""
from datetime import datetime
from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, Field, create_model

from agents_lab.core.llm import LLM
from agents_lab.core.relevance import Relevance, tfidf_relevance

Kind = Literal["observation", "action", "plan", "reflection"]
IMPORTANCE_SYSTEM = ("You rate memories. On a scale of 1 to 10, 1 is purely mundane (brushing teeth, making the "
                     "bed) and 10 is extremely poignant (a break-up, a college acceptance). Reply with JSON only.")


class Memory(BaseModel):
    id: int
    kind: Kind
    text: str
    created: datetime
    last_access: datetime
    importance: int = Field(ge=1, le=10)
    evidence: list[int] = []  # reflections: ids of the memories they were inferred from


def rating_schema(n: int) -> type[BaseModel]:
    return create_model("Ratings", ratings=(list[Annotated[int, Field(ge=1, le=10)]],
                                            Field(min_length=n, max_length=n)))


def minmax(x: np.ndarray) -> np.ndarray:
    span = x.max() - x.min()
    return np.ones_like(x, dtype=float) if span == 0 else (x - x.min()) / span


class MemoryStream:
    def __init__(self, llm: LLM, owner: str, weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
                 relevance: Relevance = tfidf_relevance, decay: float = 0.995):
        self.llm, self.owner, self.weights, self.relevance, self.decay = llm, owner, weights, relevance, decay
        self.memories: list[Memory] = []
        self.importance_since_reflection = 0

    def add_many(self, items: list[tuple[Kind, str]], now: datetime, evidence: list[list[int]] | None = None,
                 count_for_reflection: bool = True) -> list[Memory]:
        """Store memories; their importance is rated in ONE model call."""
        if not items:
            return []
        listing = "\n".join(f"{i}. {t}" for i, (_, t) in enumerate(items, 1))
        user = (f"These are memories of {self.owner}.\n{listing}\n\nTask: rate the importance of each memory, "
                f"in order. Return ratings: a list of exactly {len(items)} integers from 1 to 10.")
        r = self.llm.structured(IMPORTANCE_SYSTEM, user, rating_schema(len(items)), tag="importance", judge=True,
                                max_tokens=30 + 6 * len(items))
        new = [Memory(id=len(self.memories) + i, kind=k, text=t, created=now, last_access=now, importance=imp,
                      evidence=(evidence or [[]] * len(items))[i])
               for i, ((k, t), imp) in enumerate(zip(items, r.ratings))]
        self.memories += new
        if count_for_reflection:
            self.importance_since_reflection += sum(m.importance for m in new)
        self.llm.run.log("memories_added", owner=self.owner, memories=[m.model_dump(mode="json") for m in new])
        return new

    def scores(self, query: str, now: datetime) -> np.ndarray:
        hours = np.array([(now - m.last_access).total_seconds() / 3600 for m in self.memories])
        rec = self.decay ** np.maximum(hours, 0)
        imp = np.array([m.importance for m in self.memories], dtype=float)
        rel = self.relevance(query, [m.text for m in self.memories])
        w = self.weights
        return w[0] * minmax(rec) + w[1] * minmax(imp) + w[2] * minmax(rel)

    def retrieve(self, query: str, now: datetime, k: int = 8, token_budget: int = 600) -> list[Memory]:
        """Top-k by score that fit the token budget (a memory that doesn't fit is skipped, not cut)."""
        if not self.memories:
            return []
        s = self.scores(query, now)
        picked, used = [], 0
        for i in np.argsort(-s, kind="stable"):
            m = self.memories[i]
            t = self.llm.estimate_tokens(m.text)
            if len(picked) == k:
                break
            if used + t <= token_budget:
                picked.append(m)
                used += t
        for m in picked:
            m.last_access = now
        self.llm.run.log("retrieve", owner=self.owner, query=query, ids=[m.id for m in picked],
                         scores=[round(float(s[m.id]), 3) for m in picked])
        return picked

    def recent(self, token_budget: int) -> list[Memory]:
        """Most recent memories (newest first) that fit the budget."""
        out, used = [], 0
        for m in reversed(self.memories):
            used += self.llm.estimate_tokens(m.text)
            if used > token_budget:
                break
            out.append(m)
        return out
