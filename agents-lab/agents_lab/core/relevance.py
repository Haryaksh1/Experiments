"""Relevance functions: (query, docs) -> similarity per doc in [0, 1]. Swap in another callable to change it."""
from collections.abc import Callable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

Relevance = Callable[[str, list[str]], np.ndarray]


def tfidf_relevance(query: str, docs: list[str]) -> np.ndarray:
    if not docs:
        return np.zeros(0)
    try:
        m = TfidfVectorizer(stop_words="english").fit_transform(docs + [query])
    except ValueError:  # empty vocabulary (only stop words)
        return np.zeros(len(docs))
    return cosine_similarity(m[-1], m[:-1]).ravel()
