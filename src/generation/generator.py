"""
answer generation with source citations.

Takes the grading decision, the usable local chunks, and any
web search results, then synthesises a cited, safety-conscious
answer via Gemini. Three paths:

  relevant   -> local context only, no web
  ambiguous  -> local context + web results together
  irrelevant -> web results only, clearly labelled as not from SOP corpus
"""

from __future__ import annotations

from typing import Literal

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings
from src.websearch.search import format_web_results, web_search

# Hardcoded — too safety-critical to be probabilistic (retrieval might
# miss them; static context ensures they always appear).
HELPLINE_BLOCK = """
Emergency helplines (always valid regardless of query):
- ASDMA (Assam State Disaster Management Authority): 1070 / 1079
- National Disaster Management: 1078
- India General Emergency: 112
- NDRF (National Disaster Response Force): 011-24363260
""".strip()

SYSTEM_PROMPT = """You are Plabon, a professional flood and disaster relief assistant \
for Assam, India. You answer questions about flood preparedness, response procedures, \
evacuation, relief, and disaster management.

Rules you must follow:
1. Only make claims that are directly supported by the provided context. Never invent \
evacuation routes, shelter locations, or water levels.
2. Cite every factual claim using the format [Source: <filename>, p.<page>] for document \
context, or [Web: <url>] for web search results.
3. If context is insufficient, say so clearly and direct the user to official sources.
4. Always append the emergency helpline block at the end of every response — never omit it.
5. Use plain, clear language. This information may be read by people in an active emergency.
6. If a query involves current/live conditions (water levels, active warnings), explicitly \
note that your document knowledge base is static and the user should check live sources."""

RELEVANT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Answer the question using ONLY the document excerpts below.

Question: {query}

Document excerpts:
{context}

Emergency helplines to append:
{helplines}"""),
])

AMBIGUOUS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """Answer the question using both the document excerpts and the live web \
search results below. Where they differ, prefer the web results for current conditions \
and the documents for SOPs/procedures.

Question: {query}

Document excerpts:
{context}

Live web search results (from authoritative government sources):
{web_context}

Emergency helplines to append:
{helplines}"""),
])

IRRELEVANT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """The local document knowledge base did not contain relevant information \
for this question. Answer using ONLY the live web search results below. Clearly note \
that this answer is not sourced from the SOP document corpus.

Question: {query}

Live web search results (from authoritative government sources):
{web_context}

Emergency helplines to append:
{helplines}"""),
])


def _format_local_context(chunks: list[Document]) -> str:
    if not chunks:
        return "(no relevant local context)"
    lines = []
    for doc in chunks:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        lines.append(f"[Source: {source}, p.{page}]\n{doc.page_content}\n")
    return "\n".join(lines)


def generate_answer(
    query: str,
    path: Literal["relevant", "ambiguous", "irrelevant"],
    chunks: list[Document],
) -> dict:
    """
    Generate a cited answer. Fetches web search results automatically when
    path is ambiguous or irrelevant. Returns a dict with keys:
        answer   - the final response string
        path     - the grading path taken
        sources  - unique list of (source, page) pairs from local chunks used
        web_used - True if web results were incorporated
    """
    llm = ChatGoogleGenerativeAI(
        model=settings.generation_model,
        google_api_key=settings.google_api_key,
        temperature=0.1,
    )

    local_context = _format_local_context(chunks)
    web_results: list[dict] = []
    web_context_text = ""

    if path in ("ambiguous", "irrelevant"):
        web_results = web_search(query)
        web_context_text = format_web_results(web_results) or "(no web results returned)"

    if path == "relevant":
        chain = RELEVANT_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "context": local_context,
            "helplines": HELPLINE_BLOCK,
        })
    elif path == "ambiguous":
        chain = AMBIGUOUS_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "context": local_context,
            "web_context": web_context_text,
            "helplines": HELPLINE_BLOCK,
        })
    else:  # irrelevant
        chain = IRRELEVANT_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "web_context": web_context_text,
            "helplines": HELPLINE_BLOCK,
        })

    sources = list({
        (doc.metadata.get("source", "unknown"), doc.metadata.get("page", "?"))
        for doc in chunks
    })

    return {
        "answer": response.content,
        "path": path,
        "sources": sources,
        "web_used": path in ("ambiguous", "irrelevant"),
        "web_results": web_results,
    }


if __name__ == "__main__":
    import sys

    from src.grading.grader import corrective_retrieve
    from src.retrieval.retriever import retrieve

    query = " ".join(sys.argv[1:]) or "What should I keep in an emergency kit before a flood?"
    print(f"Query: {query}\n{'='*60}")

    retrieved = retrieve(query)
    grading_result = corrective_retrieve(query, retrieved)
    path = grading_result["path"]
    chunks = grading_result["chunks"]

    print(f"Grading decision: {path.upper()} | Usable chunks: {len(chunks)}")
    print("Generating answer...\n")

    result = generate_answer(query, path, chunks)

    print(result["answer"])
    print(f"\n{'='*60}")
    print(f"Path taken : {result['path'].upper()}")
    print(f"Web used   : {result['web_used']}")
    print(f"Local docs : {len(result['sources'])} source(s)")