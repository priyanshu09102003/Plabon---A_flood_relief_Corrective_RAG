"""
structure-aware chunking.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings


SECTION_SEPARATORS = [
    "\nSECTION ",
    "\nCHAPTER ",
    "\nPART ",
    "\n\n",
    "\n",
    ". ",
    " ",
    "",
]


def _merge_pages(page_documents: list[Document]) -> tuple[str, list[tuple[int, int]]]:
    
    text_parts = []
    breakpoints: list[tuple[int, int]] = []
    offset = 0

    for doc in page_documents:
        breakpoints.append((offset, doc.metadata["page"]))
        text_parts.append(doc.page_content)
        text_parts.append("\n")
        offset += len(doc.page_content) + 1

    return "".join(text_parts), breakpoints


def _page_for_offset(offset: int, breakpoints: list[tuple[int, int]]) -> int:
    page = breakpoints[0][1]
    for bp_offset, bp_page in breakpoints:
        if bp_offset > offset:
            break
        page = bp_page
    return page


def chunk_source_documents(page_documents: list[Document]) -> list[Document]:
    """Chunk all pages belonging to ONE source file (group by source before calling)."""
    if not page_documents:
        return []

    source_name = page_documents[0].metadata["source"]
    file_type = page_documents[0].metadata.get("file_type", "unknown")
    full_text, breakpoints = _merge_pages(page_documents)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=SECTION_SEPARATORS,
    )
    raw_chunks = splitter.create_documents([full_text])

    chunks: list[Document] = []
    search_pos = 0
    for i, raw_chunk in enumerate(raw_chunks):
        start = full_text.find(raw_chunk.page_content, search_pos)
        if start == -1:
            start = search_pos
        page = _page_for_offset(start, breakpoints)
        search_pos = start + 1

        chunks.append(
            Document(
                page_content=raw_chunk.page_content.strip(),
                metadata={
                    "source": source_name,
                    "file_type": file_type,
                    "page": page,
                    "chunk_index": i,
                },
            )
        )

    return chunks


def chunk_documents(all_documents: list[Document]) -> list[Document]:
    """Group a mixed corpus by source file and chunk each one independently."""
    by_source: dict[str, list[Document]] = {}
    for doc in all_documents:
        by_source.setdefault(doc.metadata["source"], []).append(doc)

    all_chunks: list[Document] = []
    for source_name, page_docs in by_source.items():
        page_docs_sorted = sorted(page_docs, key=lambda d: d.metadata["page"])
        all_chunks.extend(chunk_source_documents(page_docs_sorted))

    return all_chunks


if __name__ == "__main__":
    import sys
    import logging

    from src.ingestion.loaders import load_directory

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"

    print(f"Loading documents from {target_dir}...")
    docs = load_directory(target_dir)
    print(f"Loaded {len(docs)} page-document(s)\n")

    print("Chunking...")
    chunks = chunk_documents(docs)
    print(f"\nProduced {len(chunks)} chunk(s) from {len(docs)} page(s)")

    if chunks:
        print("\nFirst chunk preview:")
        print(f"  source: {chunks[0].metadata['source']}")
        print(f"  page:   {chunks[0].metadata['page']}")
        print(f"  chars:  {len(chunks[0].page_content)}")
        print(f"  text:   {chunks[0].page_content[:300]}...")

        chunk_sizes = [len(c.page_content) for c in chunks]
        print(
            f"\nChunk size stats: min={min(chunk_sizes)}, "
            f"max={max(chunk_sizes)}, avg={sum(chunk_sizes)//len(chunk_sizes)}"
        )