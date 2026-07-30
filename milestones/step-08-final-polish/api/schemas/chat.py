"""
api/schemas/chat.py
-------------------
GraphChatEngine – Pydantic Schemas for Chat Endpoint

Defines the exact shape of request and response payloads for POST /chat.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request model for POST /chat endpoint.
    """

    question: str = Field(
        ...,
        description="Question to query against the Neo4j Knowledge Graph.",
        example="How many customers are there?",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "How many customers are there?"
            }
        }
    }


class ChatResponse(BaseModel):
    """
    Response model for POST /chat endpoint.
    """

    answer: str = Field(
        ...,
        description="Natural language or structured text response based on Neo4j query execution.",
        example="There are 20 customers.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "There are 20 customers."
            }
        }
    }
