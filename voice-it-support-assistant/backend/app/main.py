"""
FastAPI Main Application Entry Point.
Initializes CORS, Knowledge Base Lifespan, and API Routes.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router
from app.knowledge.loader import sop_loader
from app.knowledge.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load SOPs and initialize dense vector index
    logger.info("Starting up Voice-Based IT Support Assistant backend...")
    docs = sop_loader.load_all()
    logger.info(f"Loaded {len(docs)} SOP documents into knowledge base.")
    vector_store.build_index()
    logger.info("Dense vector index initialized successfully.")
    yield
    # Shutdown
    logger.info("Shutting down Voice-Based IT Support Assistant backend.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Grounded Dialogue Management for Voice-Based IT Support Helpdesk",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "mock_mode": settings.is_mock_mode,
        "sops_loaded": len(sop_loader.all()),
        "endpoints": {
            "api_docs": "/docs",
            "websocket": f"/api/v1/dialogue/ws/{{session_id}}",
            "sops": "/api/v1/sops/",
            "transcribe": "/api/v1/audio/transcribe",
            "synthesize": "/api/v1/audio/synthesize",
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "vector_store_indexed": vector_store.is_indexed,
        "total_sops": len(sop_loader.all())
    }
