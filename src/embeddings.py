"""
embeddings.py
-------------
Wraps a local sentence-transformers model so the rest of the app never has
to touch the underlying library directly. Local embeddings mean the
knowledge base can be built and searched for free, with no API key.
"""
from __future__ import annotations

from functools import lru_cache

from .config import EMBEDDING_MODEL_NAME


class EmbeddingModel:
    """Thin wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        # Imported lazily so the rest of the app can be explored / tested
        # without paying the (one-time) cost of importing torch.
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str], batch_size: int = 32, show_progress: bool = False) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,   # so cosine similarity == dot product
        )
        return vectors.tolist()

    def encode_query(self, query: str) -> list[float]:
        return self.encode([query])[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """Cached singleton so the (relatively slow) model load happens once
    per process. Streamlit's own @st.cache_resource wraps this again at
    the UI layer to survive script reruns."""
    return EmbeddingModel()
