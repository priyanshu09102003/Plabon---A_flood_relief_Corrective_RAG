"""
load -> chunk -> filter -> embed -> store.

"""

from __future__ import annotations

import logging
import sys

from config import settings
from src.chunking.splitter import chunk_documents
from src.ingestion.loaders import load_directory
from src.vectorstore.chroma_store import build_index

MIN_CHUNK_CHARS = 20  
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main(target_dir: str) -> None:
    print(f"Loading documents from {target_dir}...")
    docs = load_directory(target_dir)
    print(f"Loaded {len(docs)} page-document(s)")

    print("Chunking...")
    chunks = chunk_documents(docs)
    print(f"Produced {len(chunks)} chunk(s) before filtering")

    chunks = [c for c in chunks if len(c.page_content.strip()) >= MIN_CHUNK_CHARS]
    print(f"{len(chunks)} chunk(s) remain after dropping fragments under {MIN_CHUNK_CHARS} chars")

    print("\nEmbedding and storing in ChromaDB (first run downloads the model, ~80MB, once)...")
    store = build_index(chunks)

    final_count = store.get()["ids"]
    print(f"\nDone. Collection '{settings.chroma_collection_name}' now holds {len(final_count)} chunk(s).")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    main(target)