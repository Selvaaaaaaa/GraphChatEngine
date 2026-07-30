"""
api/main.py
-----------
GraphChatEngine – API Service
FastAPI application entry point.

Milestone 01: Project Foundation
- Provides basic health and root endpoints only.
- No Kafka, Neo4j, or CSV logic in this milestone.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="GraphChatEngine API",
    description="CSV → Kafka → Neo4j Chatbot backend API",
    version="0.1.0",
)

# Allow the UI (running on a different origin during development) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Root", tags=["Status"])
async def root() -> dict:
    """Return a simple status payload to confirm the service is running."""
    return {"status": "running", "service": "api"}


@app.get("/health", summary="Health Check", tags=["Status"])
async def health() -> dict:
    """Lightweight health-check endpoint for Docker / load-balancer probes."""
    return {"status": "ok"}
