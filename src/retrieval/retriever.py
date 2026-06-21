
from __future__ import annotations

from langchain_core.documents import Document

from config import settings
from src.vectorstore.chroma_store import get_vectorstore


def retrieve(
    query: str,
    k: int | None = None,
    source_filter: str | None = None,
) -> list[tuple[Document, float]]:
    
    store = get_vectorstore()
    top_k = k or settings.retrieval_top_k

    fetch_k = top_k * 4 if source_filter else top_k
    results = store.similarity_search_with_score(query, k=fetch_k)

    if source_filter:
        results = [
            (doc, score)
            for doc, score in results
            if source_filter.lower() in doc.metadata.get("source", "").lower()
        ]
        results = results[:top_k]

    return results


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "What should I do during a flood evacuation?"
    print(f"Query: {query}\n")

    results = retrieve(query)
    for i, (doc, score) in enumerate(results, 1):
        print(f"--- Result {i} (distance={score:.4f}) ---")
        print(f"source: {doc.metadata.get('source')} | page: {doc.metadata.get('page')}")
        print(doc.page_content[:300])
        print()