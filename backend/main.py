"""FastAPI application entrypoint for NutriFit AI."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import ROOT_DIR, settings
from .database import Base, engine
from .routers import activity, auth, dashboard, dietician, meal, rag_chat
from .services import rag_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("nutrifit")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5000", "http://127.0.0.1:5000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve uploaded media so the frontend can render images via /uploads/...
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

    app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
    app.include_router(meal.router, prefix=settings.API_V1_PREFIX)
    app.include_router(rag_chat.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dietician.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dietician.consultation_router, prefix=settings.API_V1_PREFIX)
    app.include_router(activity.router, prefix=settings.API_V1_PREFIX)
    app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    def on_startup() -> None:
        # Make sure tables exist if init_db wasn't run
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as exc:
            logger.warning("Could not auto-create tables (run init_db.py): %s", exc)

        if settings.RAG_REBUILD:
            logger.info("RAG_REBUILD=True; building FAISS index from rag_data/...")
            try:
                rag_service.rebuild_vector_store()
            except Exception as exc:
                logger.exception("RAG rebuild failed: %s", exc)
        else:
            try:
                rag_service.get_vector_store()
            except Exception as exc:
                logger.warning("RAG warmup skipped: %s", exc)

    @app.get("/")
    def root() -> dict:
        return {"app": settings.PROJECT_NAME, "status": "ok"}

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
