"""
corrective grading in C-RAG.

A single Gemini Flash call grades every retrieved chunk against the
query as relevant / ambiguous / irrelevant, then a simple aggregation rule
decides which of three paths to take:

  - relevant only  -> answer from local context alone
  - any ambiguous  -> supplement local context with web search
  - all irrelevant -> discard local context, answer from web search only

Grading all chunks in one call (instead of one call per chunk) keeps this
cheap — one Flash-Lite call per query, not k of them.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from config import settings

GRADING_PROMPT = ChatPromptTemplate.from_template(
    """You are grading whether retrieved document excerpts actually answer a \
user's question, for a flood/disaster-relief assistant. Be strict: a chunk \
that's topically related but doesn't actually address what was asked should \
NOT be marked relevant.

Labels:
- relevant: directly answers, or contains a specific fact needed to answer, the question
- ambiguous: on-topic and partially useful, but likely incomplete — especially \
true for anything time-sensitive (current water levels, today's warnings, live \
conditions) that a static document can't fully cover
- irrelevant: doesn't address the question at all

Question: {query}

Excerpts:
{excerpts}

Grade every excerpt by its number."""
)


class ChunkGrade(BaseModel):
    chunk_number: int = Field(description="Matches the excerpt's number in the provided list")
    label: Literal["relevant", "ambiguous", "irrelevant"]
    reason: str = Field(description="One brief sentence explaining the label")


class GradingResult(BaseModel):
    grades: list[ChunkGrade]


def _format_excerpts(retrieved: list[tuple[Document, float]]) -> str:
    lines = []
    for i, (doc, _score) in enumerate(retrieved, 1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        lines.append(f"[{i}] (source: {source}, page: {page})\n{doc.page_content}\n")
    return "\n".join(lines)


def grade_chunks(query: str, retrieved: list[tuple[Document, float]]) -> list[ChunkGrade]:
    if not retrieved:
        return []

    llm = ChatGoogleGenerativeAI(
        model=settings.grader_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )
    structured_llm = llm.with_structured_output(GradingResult)

    excerpts_text = _format_excerpts(retrieved)
    chain = GRADING_PROMPT | structured_llm
    result: GradingResult = chain.invoke({"query": query, "excerpts": excerpts_text})

    return result.grades


def decide_path(grades: list[ChunkGrade]) -> Literal["relevant", "ambiguous", "irrelevant"]:
    labels = {g.label for g in grades}
    if "ambiguous" in labels:
        return "ambiguous"
    if "relevant" in labels:
        return "relevant"
    return "irrelevant"


def corrective_retrieve(query: str, retrieved: list[tuple[Document, float]]) -> dict:
    grades = grade_chunks(query, retrieved)
    path = decide_path(grades)

    grade_by_number = {g.chunk_number: g for g in grades}
    usable_chunks = [
        doc
        for i, (doc, _score) in enumerate(retrieved, 1)
        if grade_by_number.get(i) and grade_by_number[i].label in ("relevant", "ambiguous")
    ]

    return {
        "path": path,
        "chunks": usable_chunks,
        "grades": grades,
    }


if __name__ == "__main__":
    import sys

    from src.retrieval.retriever import retrieve

    query = " ".join(sys.argv[1:]) or "What is the current water level at the Tezpur gauge station?"
    print(f"Query: {query}\n")

    retrieved = retrieve(query)
    print(f"Retrieved {len(retrieved)} chunk(s), grading...\n")

    result = corrective_retrieve(query, retrieved)

    for i, (doc, _score) in enumerate(retrieved, 1):
        grade = next((g for g in result["grades"] if g.chunk_number == i), None)
        label = grade.label if grade else "?"
        reason = grade.reason if grade else ""
        print(f"[{i}] {label.upper():10} source={doc.metadata.get('source')} p.{doc.metadata.get('page')}")
        print(f"     reason: {reason}")

    print(f"\nDecision: {result['path'].upper()}")
    print(f"Usable chunks for generation: {len(result['chunks'])}")