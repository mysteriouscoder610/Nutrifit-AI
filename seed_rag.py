"""Embed rag_data/*.txt|*.md and upsert into the Pinecone index.

Run after `init_db.py`:
    python seed_rag.py

Requires PINECONE_API_KEY and GEMINI_API_KEY in .env. Creates the
Pinecone index (settings.PINECONE_INDEX_NAME) if it does not yet exist.
"""
from __future__ import annotations

from backend.config import settings
from backend.services import rag_service


def main() -> None:
    if not settings.PINECONE_API_KEY:
        raise SystemExit(
            "PINECONE_API_KEY is empty. Add it to your .env before running seed_rag.py."
        )
    print(
        f"Building Pinecone index '{settings.PINECONE_INDEX_NAME}' "
        f"({settings.PINECONE_CLOUD}/{settings.PINECONE_REGION}, "
        f"{settings.PINECONE_EMBED_DIM} dim) from rag_data/ …"
    )
    store = rag_service.rebuild_vector_store()
    if store is None:
        print("No documents found in rag_data/. Add .txt or .md files and re-run.")
    else:
        print("Pinecone index seeded successfully.")


if __name__ == "__main__":
    main()
