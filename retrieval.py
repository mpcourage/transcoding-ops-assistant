"""Minimal TF-IDF retrieval over the runbook corpus.

No embedding API or vector DB — this is a from-scratch cosine-similarity
search over term frequencies, deliberately dependency-light (stdlib only)
so the retrieval step runs instantly and needs no network access or API
key. Swap this for a real embedding index if the corpus grows past a few
hundred docs; at runbook-corpus scale, TF-IDF retrieves correctly and is
trivial to audit.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Below this cosine score, a match is noise (incidental shared stopwords/
# terms) rather than a genuine topical hit. Calibrated empirically: true
# matches on this corpus score 0.3-0.55, unrelated queries top out ~0.04.
_MIN_RELEVANCE_SCORE = 0.1


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class RunbookDoc:
    path: str
    title: str
    text: str


class RunbookIndex:
    def __init__(self, runbooks_dir: Path):
        self.docs: list[RunbookDoc] = []
        self._doc_tf: list[dict[str, int]] = []
        self._df: dict[str, int] = {}
        self._load(runbooks_dir)
        self._build_index()

    def _load(self, runbooks_dir: Path) -> None:
        for path in sorted(runbooks_dir.glob("*.md")):
            text = path.read_text()
            first_line = text.splitlines()[0] if text else path.stem
            title = first_line.lstrip("#").strip() or path.stem
            rel_path = f"runbooks/{path.name}"
            self.docs.append(RunbookDoc(path=rel_path, title=title, text=text))

    def _build_index(self) -> None:
        for doc in self.docs:
            tokens = _tokenize(doc.text)
            tf: dict[str, int] = {}
            for tok in tokens:
                tf[tok] = tf.get(tok, 0) + 1
            self._doc_tf.append(tf)
            for tok in tf:
                self._df[tok] = self._df.get(tok, 0) + 1

    def _idf(self, term: str) -> float:
        n = len(self.docs)
        df = self._df.get(term, 0)
        return math.log((n + 1) / (df + 1)) + 1.0

    def _vector(self, tf: dict[str, int]) -> dict[str, float]:
        return {term: count * self._idf(term) for term, count in tf.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[t] * b[t] for t in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, k: int = 3) -> list[dict]:
        query_tf: dict[str, int] = {}
        for tok in _tokenize(query):
            query_tf[tok] = query_tf.get(tok, 0) + 1
        query_vec = self._vector(query_tf)

        scored = []
        for doc, tf in zip(self.docs, self._doc_tf):
            doc_vec = self._vector(tf)
            score = self._cosine(query_vec, doc_vec)
            scored.append((score, doc))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        results = []
        for score, doc in scored[:k]:
            if score < _MIN_RELEVANCE_SCORE:
                continue
            snippet = " ".join(doc.text.split()[:40]) + "..."
            results.append(
                {
                    "path": doc.path,
                    "title": doc.title,
                    "score": round(score, 4),
                    "snippet": snippet,
                }
            )
        return results

    def get_full_text(self, path: str) -> str | None:
        for doc in self.docs:
            if doc.path == path:
                return doc.text
        return None
