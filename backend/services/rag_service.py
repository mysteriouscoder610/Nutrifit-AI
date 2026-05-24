"""LangChain + Pinecone-backed RAG service for diet/disease knowledge.

Embeddings: HuggingFace sentence-transformers/all-MiniLM-L6-v2 (384 dim, CPU,
normalized) — mirrors the HealthyMate reference at
/Users/ayush.jha/major_project/HealthyMate-Medical-Chatbot-Assistant/src/helper.py
"""
from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - older langchain
    from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..config import settings
from . import gemini_service
from .prompts import RAG_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_lock = Lock()
_vector_store: Optional[PineconeVectorStore] = None
_pinecone_client: Optional[Pinecone] = None
_embeddings_singleton: Optional[HuggingFaceEmbeddings] = None


def _embeddings() -> HuggingFaceEmbeddings:
    global _embeddings_singleton
    if _embeddings_singleton is None:
        _embeddings_singleton = HuggingFaceEmbeddings(
            model_name=settings.HF_EMBEDDING_MODEL,
            model_kwargs={"device": settings.HF_EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings_singleton


def _get_pinecone() -> Pinecone:
    global _pinecone_client
    if _pinecone_client is None:
        if not settings.PINECONE_API_KEY:
            raise RuntimeError(
                "PINECONE_API_KEY is not set. Add it to your .env file."
            )
        _pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
    return _pinecone_client


def _ensure_index() -> str:
    pc = _get_pinecone()
    name = settings.PINECONE_INDEX_NAME
    if not pc.has_index(name):
        logger.info("Creating Pinecone index %s (%d dim)", name, settings.PINECONE_EMBED_DIM)
        pc.create_index(
            name=name,
            dimension=settings.PINECONE_EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=settings.PINECONE_CLOUD,
                region=settings.PINECONE_REGION,
            ),
        )
    return name


def _load_documents(data_dir: Path) -> List[Document]:
    docs: List[Document] = []
    if not data_dir.exists():
        return docs
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def _build_index() -> Optional[PineconeVectorStore]:
    docs = _load_documents(settings.RAG_DATA_DIR)
    if not docs:
        logger.warning("No RAG data found in %s", settings.RAG_DATA_DIR)
        return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
    chunks = splitter.split_documents(docs)
    index_name = _ensure_index()
    store = PineconeVectorStore.from_documents(
        documents=chunks,
        index_name=index_name,
        embedding=_embeddings(),
    )
    logger.info("Upserted %d chunks into Pinecone index %s", len(chunks), index_name)
    return store


def get_vector_store() -> Optional[PineconeVectorStore]:
    global _vector_store
    with _lock:
        if _vector_store is not None and not settings.RAG_REBUILD:
            return _vector_store
        try:
            index_name = _ensure_index()
            _vector_store = PineconeVectorStore.from_existing_index(
                index_name=index_name,
                embedding=_embeddings(),
            )
            return _vector_store
        except Exception as exc:
            logger.exception("Failed to load Pinecone index, attempting rebuild: %s", exc)
            _vector_store = _build_index()
            return _vector_store


def rebuild_vector_store() -> Optional[PineconeVectorStore]:
    global _vector_store
    with _lock:
        _vector_store = _build_index()
        return _vector_store


def retrieve(query: str, k: int = 4) -> List[Tuple[Document, float]]:
    store = get_vector_store()
    if store is None:
        return []
    return store.similarity_search_with_score(query, k=k)


def answer_with_rag(question: str, *, context_hint: Optional[str] = None) -> dict:
    hits = retrieve(question, k=4)
    context_blocks = []
    sources = []
    for i, (doc, _score) in enumerate(hits, start=1):
        snippet = doc.page_content.strip().replace("\n\n", "\n")
        if len(snippet) > 700:
            snippet = snippet[:700] + "…"
        context_blocks.append(f"[{i}] {doc.metadata.get('source','doc')}:\n{snippet}")
        sources.append(
            {"title": doc.metadata.get("source", f"chunk-{i}"), "snippet": snippet[:240]}
        )

    context = "\n\n".join(context_blocks) if context_blocks else "(no relevant context found)"
    extra = f"\n\nAdditional image-derived context: {context_hint}" if context_hint else ""

    prompt = (
        f"{RAG_SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n\nUSER QUESTION:\n{question}{extra}\n\n"
        "Answer:"
    )
    answer = gemini_service.generate_text(prompt, model=settings.GEMINI_FLASH_MODEL)
    return {"answer": answer, "sources": sources}
