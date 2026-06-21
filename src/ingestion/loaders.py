"""
Document loaders.

Walks data/raw/, loads PDFs and plain text files into LangChain Document
objects, and falls back to OCR for scanned PDFs where normal text
extraction returns near-empty pages. Government flood SOPs are frequently
scanned, so this fallback matters more here than in a typical RAG project.

Every page is cached to data/processed/page_cache/ as it's processed, so
OCR on a given file only ever runs once — and if interrupted partway
through, the next run resumes from the last completed page instead of
starting over.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import fitz
from langchain_core.documents import Document

from config import settings

logger = logging.getLogger(__name__)


MIN_CHARS_PER_PAGE = 40

try:
    import pytesseract
    from pdf2image import convert_from_path

    OCR_AVAILABLE = True

    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

except ImportError:
    OCR_AVAILABLE = False
    logger.warning(
        "pytesseract/pdf2image not installed, or their system binaries "
        "(tesseract-ocr, poppler-utils) are missing. Scanned PDFs with no "
        "extractable text will be skipped. See README for install steps."
    )

PROCESSED_DIR = Path(settings.processed_data_dir) / "page_cache"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(source_name: str) -> Path:
    return PROCESSED_DIR / f"{Path(source_name).stem}.json"


def _load_cache(source_name: str) -> dict:
    """Returns {page_number: cached_page_dict} for whatever's already been processed."""
    cache_file = _cache_path(source_name)
    if not cache_file.exists():
        return {}
    try:
        pages = json.loads(cache_file.read_text(encoding="utf-8"))
        return {p["metadata"]["page"]: p for p in pages}
    except Exception as e:
        logger.warning(f"Cache for {source_name} unreadable ({e}), starting fresh.")
        return {}


def _write_cache(source_name: str, cached_by_page: dict) -> None:
    ordered = sorted(cached_by_page.values(), key=lambda p: p["metadata"]["page"])
    _cache_path(source_name).write_text(json.dumps(ordered, indent=2), encoding="utf-8")


def _ocr_page(pdf_path: str, page_number: int) -> str:
    """Render one PDF page to an image and OCR it. Returns empty string on failure."""
    if not OCR_AVAILABLE or not settings.ocr_enabled:
        return ""
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page_number + 1,
            last_page=page_number + 1,
            dpi=settings.ocr_dpi,
            poppler_path=settings.poppler_path or None,
        )
        return pytesseract.image_to_string(images[0]) if images else ""
    except Exception as e:
        logger.warning(f"OCR failed on {pdf_path} page {page_number + 1}: {e}")
        return ""


def load_pdf(path: str) -> list[Document]:
    source_name = Path(path).name
    cached_by_page = _load_cache(source_name)

    with fitz.open(path) as pdf:
        total_pages = len(pdf)

        if len(cached_by_page) >= total_pages:
            logger.info(f"  {source_name}: fully cached ({total_pages} page(s)), skipping reprocessing")
        else:
            logger.info(f"  {source_name}: {total_pages} page(s), {len(cached_by_page)} already cached")

            for page_number, page in enumerate(pdf):
                page_num = page_number + 1
                if page_num in cached_by_page:
                    continue  # already done — resume past it

                text = page.get_text().strip()

                if len(text) < MIN_CHARS_PER_PAGE:
                    logger.info(f"  page {page_num}/{total_pages}: sparse text, running OCR...")
                    ocr_text = _ocr_page(path, page_number).strip()
                    if len(ocr_text) > len(text):
                        text = ocr_text
                        extraction_method = "ocr"
                    else:
                        extraction_method = "native_sparse"
                else:
                    extraction_method = "native"

                if text:
                    cached_by_page[page_num] = {
                        "page_content": text,
                        "metadata": {
                            "source": source_name,
                            "page": page_num,
                            "file_type": "pdf",
                            "extraction_method": extraction_method,
                        },
                    }
                    _write_cache(source_name, cached_by_page)  # checkpoint after every page

    ordered = sorted(cached_by_page.values(), key=lambda p: p["metadata"]["page"])
    return [Document(page_content=p["page_content"], metadata=p["metadata"]) for p in ordered]


def load_text(path: str) -> list[Document]:
    source_name = Path(path).name
    text = Path(path).read_text(encoding="utf-8")
    return [
        Document(
            page_content=text,
            metadata={"source": source_name, "page": 1, "file_type": "txt"},
        )
    ]


def load_directory(dir_path: str) -> list[Document]:
    documents: list[Document] = []
    loaders_by_suffix = {".pdf": load_pdf, ".txt": load_text}

    for file_path in sorted(Path(dir_path).iterdir()):
        loader = loaders_by_suffix.get(file_path.suffix.lower())
        if loader is None:
            continue
        logger.info(f"Loading {file_path.name}")
        documents.extend(loader(str(file_path)))

    return documents


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
    docs = load_directory(target_dir)
    print(f"\nLoaded {len(docs)} document(s) from {target_dir}")
    if docs:
        print("\nFirst document preview:")
        print(f"  source: {docs[0].metadata['source']}")
        print(f"  page:   {docs[0].metadata.get('page')}")
        print(f"  text:   {docs[0].page_content[:200]}...")