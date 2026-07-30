"""
api/routers/ingest.py
---------------------
GraphChatEngine – Ingest Router

Milestone 03: Kafka Producer

Thin HTTP layer — handles only:
  - Request parsing (UploadFile)
  - Calling the service layer
  - Mapping service results / errors to HTTP responses

No business logic and no Kafka code lives here.
"""

import logging

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from api.schemas.ingest import ErrorResponse, IngestPublishedResponse
from api.services.ingest_service import CSVValidationError, process_csv_upload
from api.services.kafka_producer import KafkaPublishError

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
    summary="Upload a CSV file and publish rows to Kafka",
    description=(
        "Accepts a **multipart/form-data** CSV file upload, runs structural "
        "validation, then publishes every row as a JSON message to the "
        "`customer-data` Kafka topic. Returns a publish summary."
        "\n\n"
        "**Accepted:** `.csv` files only. "
        "\n\n"
        "**Rejected:** `.pdf`, `.xlsx`, `.png`, `.jpg`, `.zip`, empty files, "
        "files with no headers, and malformed CSV."
    ),
    response_model=IngestPublishedResponse,
    responses={
        200: {
            "description": "CSV validated and all rows published to Kafka.",
            "model": IngestPublishedResponse,
        },
        400: {
            "description": "File rejected — wrong type, empty, or missing headers.",
            "model": ErrorResponse,
        },
        422: {
            "description": "CSV is malformed or cannot be parsed.",
            "model": ErrorResponse,
        },
        503: {
            "description": "Kafka broker is unavailable.",
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
    Upload a CSV file, validate it, and publish every row to Kafka.

    This is the main entry point for the CSV → Kafka → Neo4j pipeline.
    In Milestone 03, it validates the file and publishes rows to Kafka.
    Neo4j writes will be added in Milestone 04.

    Parameters
    ----------
    file : UploadFile
        The CSV file submitted via multipart/form-data.

    Returns
    -------
    JSONResponse
        HTTP 200 with IngestPublishedResponse on success.
        HTTP 400/422 with ErrorResponse on validation failure.
        HTTP 503 with ErrorResponse if Kafka is unreachable.
        HTTP 500 with ErrorResponse on unexpected errors.
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

    except KafkaPublishError as exc:
        logger.error(
            "Kafka publish error | status=%d | message=%s",
            exc.http_status,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": exc.message},
        )

    except Exception as exc:
        logger.error("Unhandled exception in /ingest | error=%s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred. Please try again."},
        )
