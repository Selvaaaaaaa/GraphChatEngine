"""
api/schemas/ingest.py
---------------------
GraphChatEngine – Pydantic Schemas for the Ingest Endpoint

Defines the exact shape of the JSON that POST /ingest returns,
both on success and on failure. FastAPI uses these schemas to:
  - Validate and serialize response data
  - Auto-generate accurate Swagger / OpenAPI documentation
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class IngestSuccessResponse(BaseModel):
    """
    Returned by POST /ingest when the CSV passes all validation checks.
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
        description="Total number of data rows (excluding header).",
        example=120,
    )
    columns: int = Field(
        ...,
        description="Total number of columns.",
        example=6,
    )
    column_names: List[str] = Field(
        ...,
        description="List of column header names extracted from the CSV.",
        example=["id", "name", "email", "age", "city", "country"],
    )
    size_kb: float = Field(
        ...,
        description="File size in kilobytes, rounded to 2 decimal places.",
        example=12.4,
    )
    status: str = Field(
        default="validated",
        description="Pipeline stage — always 'validated' at this milestone.",
        example="validated",
    )
    timestamp: str = Field(
        ...,
        description="ISO-8601 UTC timestamp of when the job was created.",
        example="2026-07-30T12:00:00.000000",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "filename": "customers.csv",
                "rows": 120,
                "columns": 6,
                "column_names": ["id", "name", "email", "age", "city", "country"],
                "size_kb": 12.4,
                "status": "validated",
                "timestamp": "2026-07-30T12:00:00.000000",
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Returned by POST /ingest when the file is invalid or unreadable.
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
