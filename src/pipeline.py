"""
pipeline orchestrator.

Single entry point that wires retrieve -> grade -> generate.
The Streamlit UI calls run_pipeline() and only ever sees a clean result dict
-- grading labels, chunk scores, and source metadata are kept internal.
"""

from __future__ import annotations

import re

from src.generation.generator import generate_answer
from src.grading.grader import corrective_retrieve
from src.retrieval.retriever import retrieve


def _clean_response(text: str) -> str:
    text = re.sub(r"\[Source:[^\]]+\]", "", text)
    text = re.sub(r"\[Web:[^\]]+\]", "", text)
    text = re.sub(r"  +", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run_pipeline(query: str) -> dict:
    """
    Full C-RAG pipeline. Returns:
        answer      str   -- clean, markdown-formatted answer for st.markdown()
        web_used    bool  -- True if live web search was used
        _path       str   -- internal grading path (NEVER shown in UI)
    """
    retrieved = retrieve(query)
    grading_result = corrective_retrieve(query, retrieved)

    path = grading_result["path"]
    chunks = grading_result["chunks"]

    raw = generate_answer(query, path, chunks)

    return {
        "answer": _clean_response(raw["answer"]),
        "web_used": raw["web_used"],
        "_path": path,
    }