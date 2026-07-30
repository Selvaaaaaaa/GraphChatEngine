"""
api/schemas/ingest.py
---------------------
GraphChatEngine – Pydantic Schemas for the Ingest Endpoint

Defines the exact shape of the JSON that POST /ingest returns,
both on success and on failure. FastAPI uses these schemas to:
  - Validate and serialize response data
  - Auto-generate accurate Swagger / OpenAPI documentation

Milestone 03: Added IngestPublishedResponse with Kafka fields.
"""

from typing import List

from pydantic import BaseModel, Field


class IngestPublishedResponse(BaseModel):
    """
    Returned by POST /ingest (Milestone 03+) when CSV rows have been
    validated AND successfully published to Kafka.
    """

    job_id: str = Field(
        ...,
        description="Unique UUID4 identifier for this ingestion job.",
        example="3fa85f64-5717-4562-b3fc-2c963f66afa6",
    )
    filename: str = Field(
        ...,
        description="Original filename of the uploaded CSV.",
        example="customers.csv",
    )
    rows: int = Field(
        ...,
        description="Total number of data rows parsed from the CSV.",
        example=15,
    )
    messages_published: int = Field(
        ...,
        description="Number of Kafka messages successfully published (one per row).",
        example=15,
    )
    topic: str = Field(
        ...,
        description="Kafka topic name messages were published to.",
        example="customer-data",
    )
    status: str = Field(
        default="published",
        description="Pipeline stage — 'published' once rows reach Kafka.",
        example="published",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "filename": "customers.csv",
                "rows": 15,
                "messages_published": 15,
                "topic": "customer-data",
                "status": "published",
            }
        }
    }


class IngestSuccessResponse(BaseModel):
    """
    Legacy Milestone 02 response — kept for backward compatibility.
    Use IngestPublishedResponse for Milestone 03+.
    """

    job_id: str = Field(..., example="3fa85f64-5717-4562-b3fc-2c963f66afa6")
    filename: str = Field(..., example="customers.csv")
    rows: int = Field(..., example=120)
    columns: int = Field(..., example=6)
    column_names: List[str] = Field(..., example=["id", "name", "email", "age", "city", "country"])
    size_kb: float = Field(..., example=12.4)
    status: str = Field(default="validated", example="validated")
    timestamp: str = Field(..., example="2026-07-30T12:00:00.000000")


class ErrorResponse(BaseModel):
    """
    Returned by POST /ingest when the file is invalid, unreadable,
    or when Kafka is unavailable.
    """

    error: str = Field(
        ...,
        description="Human-readable description of what went wrong.",
        example="Only CSV files are supported.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"error": "Only CSV files are supported."}
        }
    }
