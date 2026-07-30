"""
api/routers/ingest.py
---------------------
GraphChatEngine – Ingest Router

Thin HTTP layer — handles only:
  - Request parsing (UploadFile)
  - Calling the service layer
  - Mapping service results / errors to HTTP responses

No business logic lives here.
"""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from api.schemas.ingest import ErrorResponse, IngestSuccessResponse
from api.services.ingest_service import CSVValidationError, process_csv_upload

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Router definition
# -------------------------------------------------------------------------

router = APIRouter(
    prefix="/ingest",
    tags=["Ingest"],
)


# -------------------------------------------------------------------------
# POST /ingest
# -------------------------------------------------------------------------

@router.post(
    "",
    summary="Upload and validate a CSV file",
    description=(
        "Accepts a **multipart/form-data** CSV file upload, runs structural "
        "validation, extracts metadata (row count, column names, file size), "
        "and returns a job payload that downstream services can use. "
        "\n\n"
        "**Accepted:** `.csv` files only. "
        "\n\n"
        "**Rejected:** `.pdf`, `.xlsx`, `.png`, `.jpg`, `.zip`, empty files, "
        "files with no headers, and malformed CSV."
    ),
    response_model=IngestSuccessResponse,
    responses={
        200: {
            "description": "CSV validated successfully.",
            "model": IngestSuccessResponse,
        },
        400: {
            "description": "File rejected — wrong type, empty, or missing headers.",
            "model": ErrorResponse,
        },
        422: {
            "description": "CSV is malformed or cannot be parsed.",
            "model": ErrorResponse,
        },
        500: {
            "description": "Unexpected server-side error.",
            "model": ErrorResponse,
        },
    },
)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file to ingest (multipart/form-data)."),
) -> JSONResponse:
    """
    Upload a CSV file for validation and metadata extraction.

    This endpoint is the entry point for the CSV → Kafka → Neo4j pipeline.
    In Milestone 02 it stops after validation and returns job metadata.
    Kafka production will be added in Milestone 03.

    Parameters
    ----------
    file : UploadFile
        The CSV file submitted via multipart/form-data.

    Returns
    -------
    JSONResponse
        HTTP 200 with IngestSuccessResponse payload on success, or
        HTTP 400/422/500 with ErrorResponse payload on failure.
    """
    try:
        result = await process_csv_upload(file)
        return JSONResponse(status_code=200, content=result)

    except CSVValidationError as exc:
        logger.warning(
            "CSV validation error | status=%d | message=%s",
            exc.http_status,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": exc.message},
        )

    except Exception as exc:
        # Catch-all — should not normally reach here
        logger.error("Unhandled exception in /ingest | error=%s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred. Please try again."},
        )
