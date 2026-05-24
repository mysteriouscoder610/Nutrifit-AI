"""Application configuration loaded from environment variables."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    PROJECT_NAME: str = "NutriFit AI"
    API_V1_PREFIX: str = "/api"

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_FLASH_MODEL: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv(
        "GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"
    )

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/nutrifit_db",
    )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    UPLOAD_DIR: Path = ROOT_DIR / os.getenv("UPLOAD_DIR", "uploads")
    MEAL_UPLOAD_DIR: Path = UPLOAD_DIR / "meals"
    RECORDING_UPLOAD_DIR: Path = UPLOAD_DIR / "recordings"
    DISEASE_UPLOAD_DIR: Path = UPLOAD_DIR / "disease"

    RAG_DATA_DIR: Path = ROOT_DIR / os.getenv("RAG_DATA_DIR", "rag_data")
    RAG_REBUILD: bool = os.getenv("RAG_REBUILD", "False").lower() == "true"

    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "nutrifit-rag")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_EMBED_DIM: int = int(os.getenv("PINECONE_EMBED_DIM", "384"))
    HF_EMBEDDING_MODEL: str = os.getenv(
        "HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    HF_EMBEDDING_DEVICE: str = os.getenv("HF_EMBEDDING_DEVICE", "cpu")

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    def ensure_dirs(self) -> None:
        for d in (
            self.UPLOAD_DIR,
            self.MEAL_UPLOAD_DIR,
            self.RECORDING_UPLOAD_DIR,
            self.DISEASE_UPLOAD_DIR,
            self.RAG_DATA_DIR,
        ):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = get_settings()
