"""
 ChromaDB persistent vector store.
"""

from __future__ import annotations

import logging

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import settings
from src.embeddings.embedder import get_embeddings

logger = logging.getLogger(__name__)


def get_vectorstore(embeddings: Embeddings | None = None) -> Chroma:
    
    return Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings or get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )


def build_index(
    chunks: list[Document],
    batch_size: int = 100,
    reset: bool = True,
    embeddings: Embeddings | None = None,
) -> Chroma:

    store = get_vectorstore(embeddings)

    if reset:
        existing_ids = store.get()["ids"]
        if existing_ids:
            logger.info(f"Clearing {len(existing_ids)} existing entries from '{settings.chroma_collection_name}'")
            store.delete(ids=existing_ids)

    total = len(chunks)
    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        store.add_documents(batch)
        logger.info(f"  indexed {min(i + batch_size, total)}/{total} chunk(s)")

    return store