"""
web search fallback.

Used when grading decides local context is ambiguous (supplement)
or irrelevant (replace). Restricted to authoritative government domains —
pulling flood/disaster info from a random blog or forum is actively
dangerous in this domain, so this never does an open web search.
"""

from __future__ import annotations

from ddgs import DDGS

AUTHORITATIVE_DOMAINS = [
    "ndma.gov.in",
    "asdma.assam.gov.in",
    "cwc.gov.in",
    "mausam.imd.gov.in",
]


def web_search(query: str, max_results: int = 4) -> list[dict]:

    site_filter = " OR ".join(f"site:{d}" for d in AUTHORITATIVE_DOMAINS)
    scoped_query = f"{query} ({site_filter})"

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(scoped_query, max_results=max_results))
    except Exception as e:
        print(f"Web search failed: {e}")
        return []

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "snippet": r.get("body", ""),
        }
        for r in raw_results
    ]


def format_web_results(results: list[dict]) -> str:
   
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[Web {i}] {r['title']} ({r['url']})\n{r['snippet']}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) or "current flood warning Assam"
    print(f"Searching (restricted to {', '.join(AUTHORITATIVE_DOMAINS)}): {query}\n")

    results = web_search(query)
    if not results:
        print("No results found.")
    else:
        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['title']}")
            print(f"    {r['url']}")
            print(f"    {r['snippet'][:200]}")
            print()