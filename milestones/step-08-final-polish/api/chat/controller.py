"""
api/chat/controller.py
----------------------
GraphChatEngine – Chat Controller (Router)

Milestone 06: Graph Query API and Chat Backend

Thin HTTP Layer for POST /chat:
  - Parses ChatRequest payload
  - Delegates execution to ChatService
  - Maps domain results & exceptions to HTTP JSON responses

No Cypher queries live here.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from api.chat.service import ChatService
from api.chat.repository import Neo4jChatRepositoryError
from api.schemas.chat import ChatRequest, ChatResponse
from api.schemas.ingest import ErrorResponse

logger = logging.getLogger("api.chat.controller")

# Initialize router for Chat endpoint
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

# Singleton service instance
chat_service = ChatService()


@router.post(
    "",
    summary="Query the Graph Database via Chatbot",
    description=(
        "Accepts a natural language question, matches it against predefined "
        "Cypher patterns, queries the Neo4j Knowledge Graph, and returns a "
        "structured text answer."
        "\n\n"
        "**Supported Questions:**\n"
        "- *How many customers are there?*\n"
        "- *List all customers*\n"
        "- *Show customer 1*\n"
        "- *Show customers from Chennai*\n"
        "- *Show customers from Coimbatore*\n"
        "- *Show all emails*\n"
        "- *Show all cities*\n"
    ),
    response_model=ChatResponse,
    responses={
        200: {
            "description": "Question answered successfully from Neo4j.",
            "model": ChatResponse,
        },
        400: {
            "description": "Invalid or missing question payload.",
            "model": ErrorResponse,
        },
        503: {
            "description": "Neo4j graph database unavailable.",
            "model": ErrorResponse,
        },
        500: {
            "description": "Unexpected query execution error.",
            "model": ErrorResponse,
        },
    },
)
async def ask_question(request: ChatRequest) -> JSONResponse:
    """
    Process a natural language question against Neo4j.
    """
    question = request.question.strip() if request.question else ""

    if not question:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Question field cannot be empty."},
        )

    try:
        response_payload = chat_service.process_question(question)
        return JSONResponse(status_code=status.HTTP_200_OK, content=response_payload)

    except Neo4jChatRepositoryError as exc:
        logger.error("Database error handling /chat request | status=%d | message=%s", exc.http_status, exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": exc.message},
        )

    except Exception as exc:
        logger.error("Unhandled exception in /chat endpoint | error=%s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An internal server error occurred while querying the graph."},
        )
