"""
local embedding model.

"""

from __future__ import annotations

from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

_embeddings: HuggingFaceEmbeddings | None = None


def get_embeddings() -> HuggingFaceEmbeddings:
    """Lazily load the embedding model once and reuse it across calls."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            # Normalizing means cosine similarity == dot product, which is
            # what Chroma's default distance metric expects.
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings