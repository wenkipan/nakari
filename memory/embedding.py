import hashlib
from dataclasses import dataclass
from typing import List, Protocol


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> List[float]: ...


@dataclass(frozen=True)
class FakeEmbeddingProvider:
    dim: int

    def embed(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # Map bytes to floats in [0, 1)
        vals = [b / 256.0 for b in digest]
        if self.dim <= 0:
            return []

        out: List[float] = []
        i = 0
        while len(out) < self.dim:
            out.append(vals[i % len(vals)])
            i += 1
        return out
