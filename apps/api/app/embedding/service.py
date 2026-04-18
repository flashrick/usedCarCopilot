from __future__ import annotations

import hashlib
import math
import re

DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_EMBEDDING_MODEL = "local-hash-embedding-v1"

TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")

DOMAIN_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "commute": ("commuting", "fuel", "economy", "urban"),
    "commuting": ("commute", "fuel", "economy", "urban"),
    "daily": ("commuting", "reliability", "service"),
    "family": ("passenger", "seat", "cargo", "space"),
    "reliable": ("reliability", "service", "maintenance", "condition"),
    "reliability": ("reliable", "service", "maintenance", "condition"),
    "risk": ("inspection", "condition", "warning", "repair"),
    "safe": ("inspection", "condition", "warning", "repair"),
    "cheap": ("budget", "price", "cost"),
    "budget": ("cheap", "price", "cost"),
    "hybrid": ("battery", "fuel", "economy"),
    "suv": ("cargo", "family", "space"),
    "hatchback": ("city", "parking", "compact"),
}


def chunk_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class LocalHashEmbeddingProvider:
    """Deterministic local embedding for repeatable development without API keys."""

    model = DEFAULT_EMBEDDING_MODEL
    dimensions = DEFAULT_EMBEDDING_DIMENSIONS

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        terms = list(self._weighted_terms(text))
        if not terms:
            vector[0] = 1.0
            return vector

        for term, weight in terms:
            bucket, sign = self._bucket(term)
            vector[bucket] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            vector[0] = 1.0
            return vector
        return [value / norm for value in vector]

    def _weighted_terms(self, text: str) -> list[tuple[str, float]]:
        tokens = TOKEN_PATTERN.findall(text.lower())
        terms: list[tuple[str, float]] = []
        for token in tokens:
            terms.append((token, 1.0))
            for expansion in DOMAIN_EXPANSIONS.get(token, ()):
                terms.append((expansion, 0.55))

        for index in range(len(tokens) - 1):
            terms.append((f"{tokens[index]} {tokens[index + 1]}", 1.25))
        return terms

    def _bucket(self, term: str) -> tuple[int, float]:
        digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        bucket = value % self.dimensions
        sign = 1.0 if value & 1 else -1.0
        return bucket, sign
