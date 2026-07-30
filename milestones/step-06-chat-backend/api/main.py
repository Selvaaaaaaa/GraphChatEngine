"""
api/main.py
-----------
GraphChatEngine – API Service
FastAPI application entry point.

Responsibilities of this file (ONLY):
  - Create the FastAPI application instance
  - Configure middleware
  - Register routers
  - Configure logging on startup

Milestone 02: CSV Upload & Validation
  - Adds POST /ingest via the ingest router
  - main.py contains NO business logic — all logic lives in routers/services
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.logging_config import configure_logging
from api.routers import ingest
from api.chat import router as chat_router

# ---------------------------------------------------------------------------
# Logging — configure once at module load time
# ---------------------------------------------------------------------------
configure_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="GraphChatEngine API",
    description=(
        "## CSV → Kafka → Neo4j Chatbot\n\n"
        "Production-style incremental pipeline built during a hackathon.\n\n"
        "**Milestone 06** — Graph Query API & Chat Backend is active.\n\n"
        "- Use `POST /ingest` to upload CSV files to Kafka/Neo4j.\n"
        "- Use `POST /chat` to query the Neo4j Knowledge Graph using natural language questions."
    ),
    version="0.6.0",
    contact={"name": "GraphChatEngine Team"},
    license_info={"name": "MIT"},
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — register here, implement elsewhere
# ---------------------------------------------------------------------------

app.include_router(ingest.router)
app.include_router(chat_router)

# ---------------------------------------------------------------------------
# Root & Health routes (lightweight — stay in main.py for simplicity)
# ---------------------------------------------------------------------------

@app.get("/", summary="Root", tags=["Status"])
async def root() -> dict:
    """Return a simple status payload to confirm the service is running."""
    return {"status": "running", "service": "api", "milestone": "06-chat-backend"}


@app.get("/health", summary="Health Check", tags=["Status"])
async def health() -> dict:
    """Lightweight health-check endpoint for Docker / load-balancer probes."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Log service start so Docker logs show a clear milestone banner."""
    logger.info("=" * 60)
    logger.info("GraphChatEngine API started — Milestone 06: Chat Backend")
    logger.info("Swagger UI → http://localhost:8000/docs")
    logger.info("=" * 60)
