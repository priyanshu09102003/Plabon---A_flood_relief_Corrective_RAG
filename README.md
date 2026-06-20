# Plabon — C-RAG flood relief assistant

*"Plabon" (প্লাৱন) means flood in Assamese.*

A corrective RAG (C-RAG) system over official Assam/India flood disaster
SOPs and guidelines. A relevance grader checks every retrieved chunk before
generation — if the local knowledge base is incomplete or stale for a
query, the system falls back to live web search restricted to authoritative
government domains, instead of answering from a static document set alone.

Free, local-first stack: ChromaDB (local vector store), sentence-transformers, DuckDuckGo search, and the
Gemini API  for grading and generation.

## Phase checklist

- [x] **Phase 1 — Environment setup**: project structure, dependencies, config, .env, setup-check app
- [ ] **Phase 2 — Data collection & document loading**: gather official PDFs, PyMuPDF/pdfplumber loaders, OCR fallback
- [ ] **Phase 3 — Chunking**: structure-aware splitting, tables kept as separate markdown chunks
- [ ] **Phase 4 — Embeddings & vector store**: sentence-transformers + ChromaDB ingestion script
- [ ] **Phase 5 — Retrieval**: top-k similarity search with metadata filtering (district, hazard type)
- [ ] **Phase 6 — Corrective grading**: Gemini Flash-Lite grades each chunk relevant / ambiguous / irrelevant
- [ ] **Phase 7 — Web search fallback**: DuckDuckGo search restricted to NDMA/ASDMA/CWC/IMD domains
- [ ] **Phase 8 — Generation**: cited answer synthesis, hardcoded helpline numbers, safety disclaimers
- [ ] **Phase 9 — Streamlit UI**: real chat interface replacing the Phase 1 setup-check app
- [ ] **Phase 10 — Testing & polish**: sample queries proving each grading path, README diagrams, demo recording

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# edit .env and paste your free key from https://aistudio.google.com/apikey

# 4. Verify the setup
streamlit run app.py
# click "Test Gemini connection" — you should see a success message
```

## Data sources for Phase 2

`data/raw/` currently contains only a synthetic sample document so the
pipeline can be tested end-to-end before real documents are collected.
Replace it with official PDFs from:

- NDMA — https://ndma.gov.in (national flood management guidelines)
- ASDMA — https://asdma.assam.gov.in (Assam state SOPs, district plans, toll-free numbers)
- CWC — https://cwc.gov.in (flood forecasting, river gauge danger levels)
- IMD — https://mausam.imd.gov.in (warning color classifications)

## Project structure

```
plabon-rag/
├── app.py                  # Streamlit entrypoint (setup-check for now, real UI in Phase 9)
├── config.py                # typed settings loaded from .env
├── data/
│   ├── raw/                 # source PDFs (drop official docs here in Phase 2)
│   └── processed/           # chunked output for inspection
├── src/
│   ├── ingestion/            # Phase 2
│   ├── chunking/             # Phase 3
│   ├── embeddings/           # Phase 4
│   ├── vectorstore/          # Phase 4
│   ├── retrieval/            # Phase 5
│   ├── grading/               # Phase 6 — the corrective step
│   ├── websearch/             # Phase 7
│   ├── generation/            # Phase 8
│   └── pipeline.py            # Phase 9 — wires everything together
├── scripts/
│   └── build_index.py         # Phase 2/4 — run after dropping PDFs into data/raw/
└── tests/
    └── sample_queries.py       # Phase 10
```
