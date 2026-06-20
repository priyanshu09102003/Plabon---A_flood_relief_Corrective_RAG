"""
Central configuration for Plabon.

Loads environment variables once and exposes typed settings used across the
ingestion, retrieval, grading, and generation modules. Every later phase
just does:

    from config import settings
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # --- API ---
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # --- Vector store ---
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "flood_sop_kb")

    # --- Embeddings (free, local) ---
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # --- LLMs (model tiering: cheap grader, stronger generator) ---
    grader_model: str = os.getenv("GRADER_MODEL", "gemini-2.5-flash")
    generation_model: str = os.getenv("GENERATION_MODEL", "gemini-2.5-flash")

    # --- Chunking ---
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 800))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 120))

    # --- Retrieval ---
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", 6))

    # --- Paths ---
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"

    def validate(self) -> None:
        if not self.google_api_key or self.google_api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://aistudio.google.com/apikey"
            )


settings = Settings()


if __name__ == "__main__":
    settings.validate()
    print("Config loaded successfully:")
    print(f"  Embedding model : {settings.embedding_model}")
    print(f"  Grader model    : {settings.grader_model}")
    print(f"  Generation model: {settings.generation_model}")
    print(f"  Chroma dir      : {settings.chroma_persist_dir}")
