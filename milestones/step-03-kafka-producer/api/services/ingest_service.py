"""
api/services/ingest_service.py
-------------------------------
GraphChatEngine – CSV Ingest Service

Milestone 03: Kafka Producer

This module contains all the business logic for CSV ingestion:
  1. File-type validation (extension guard)
  2. CSV parsing via pandas
  3. Structural validation (empty file, missing headers, malformed rows)
  4. Metadata extraction (rows, columns, column names, size)
  5. Job ID generation
  6. Kafka publish — each CSV row becomes one Kafka message  ← NEW M03

STOP CONDITION — Milestone 03:
  After publishing, the function returns a publish summary dict.
  It does NOT consume Kafka messages (Milestone 04).
  It does NOT write to Neo4j (Milestone 04).
"""

import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd
from fastapi import UploadFile

from api.core.config import settings
from api.services.kafka_producer import KafkaPublishError, publish_rows_to_kafka
from api.utils.file_helpers import bytes_to_kb, is_csv_filename

logger = logging.getLogger(__name__)


class CSVValidationError(Exception):
    """
    Raised when the uploaded file fails any validation check.

    Attributes
    ----------
    message : str
        Human-readable error description (returned to the client).
    http_status : int
        Suggested HTTP status code for the response.
    """

    def __init__(self, message: str, http_status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status


async def process_csv_upload(file: UploadFile) -> Dict[str, Any]:
    """
    Validate a CSV file, then publish every row to Kafka.

    Parameters
    ----------
    file : UploadFile
        The multipart file object provided by FastAPI.

    Returns
    -------
    Dict[str, Any]
        A dictionary matching IngestPublishedResponse:
        {job_id, filename, rows, messages_published, topic, status}

    Raises
    ------
    CSVValidationError
        If the file fails any validation check.
    KafkaPublishError
        If the Kafka broker is unavailable or a publish fails.
    """
    filename = file.filename or "unknown"
    logger.info("Upload started | filename=%s | content_type=%s", filename, file.content_type)

    # ------------------------------------------------------------------
    # 1. Extension check — primary guard against wrong file types
    # ------------------------------------------------------------------
    if not is_csv_filename(filename):
        logger.warning("Validation failed | reason=wrong_extension | filename=%s", filename)
        raise CSVValidationError(
            message="Only CSV files are supported. "
                    f"Received: '{filename}'. "
                    "Please upload a file with the .csv extension.",
            http_status=400,
        )

    # ------------------------------------------------------------------
    # 2. Read raw bytes from the upload stream
    # ------------------------------------------------------------------
    raw_bytes: bytes = await file.read()
    size_bytes: int = len(raw_bytes)

    if size_bytes == 0:
        logger.warning("Validation failed | reason=empty_file | filename=%s", filename)
        raise CSVValidationError(
            message="CSV file is empty. Please upload a file with content.",
            http_status=400,
        )

    # ------------------------------------------------------------------
    # 3. Parse with pandas — catches malformed CSV structures
    # ------------------------------------------------------------------
    try:
        dataframe = pd.read_csv(io.BytesIO(raw_bytes))
    except pd.errors.EmptyDataError:
        logger.warning("Validation failed | reason=empty_data | filename=%s", filename)
        raise CSVValidationError(
            message="CSV file is empty or contains no readable data.",
            http_status=400,
        )
    except pd.errors.ParserError as exc:
        logger.warning(
            "Validation failed | reason=parse_error | filename=%s | detail=%s",
            filename,
            str(exc),
        )
        raise CSVValidationError(
            message=f"Unable to parse CSV. The file may be malformed or corrupted. Detail: {exc}",
            http_status=422,
        )
    except Exception as exc:
        logger.error(
            "Unexpected error during CSV parsing | filename=%s | error=%s",
            filename,
            str(exc),
            exc_info=True,
        )
        raise CSVValidationError(
            message="An unexpected error occurred while reading the CSV file.",
            http_status=500,
        )

    # ------------------------------------------------------------------
    # 4. Structural validation — must have at least one column header
    # ------------------------------------------------------------------
    if dataframe.columns.empty:
        logger.warning("Validation failed | reason=no_headers | filename=%s", filename)
        raise CSVValidationError(
            message="CSV file is missing column headers. "
                    "The first row must contain column names.",
            http_status=400,
        )

    if dataframe.empty:
        logger.warning("Validation failed | reason=no_rows | filename=%s", filename)
        raise CSVValidationError(
            message="CSV file contains headers but has no data rows. "
                    "Please upload a file with at least one data row.",
            http_status=400,
        )

    # ------------------------------------------------------------------
    # 5. Extract metadata
    # ------------------------------------------------------------------
    num_rows: int = len(dataframe)
    size_kb: float = bytes_to_kb(size_bytes)

    logger.info(
        "Validation success | filename=%s | rows=%d | size_kb=%.2f",
        filename,
        num_rows,
        size_kb,
    )

    # ------------------------------------------------------------------
    # 6. Generate job ID
    # ------------------------------------------------------------------
    job_id: str = str(uuid.uuid4())
    logger.info("Job created | job_id=%s | filename=%s", job_id, filename)

    # ------------------------------------------------------------------
    # 7. Convert DataFrame rows to a list of dicts for Kafka
    #    - use_int64=False converts numpy int64 → Python int (JSON-safe)
    # ------------------------------------------------------------------
    rows_as_dicts = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")

    # ------------------------------------------------------------------
    # 8. Publish to Kafka — one message per row
    #    KafkaPublishError propagates up to the router unchanged
    # ------------------------------------------------------------------
    messages_published: int = publish_rows_to_kafka(
        job_id=job_id,
        rows=rows_as_dicts,
        topic=settings.kafka_topic,
    )

    logger.info(
        "Pipeline complete | job_id=%s | rows=%d | messages_published=%d | topic=%s",
        job_id,
        num_rows,
        messages_published,
        settings.kafka_topic,
    )

    return {
        "job_id": job_id,
        "filename": filename,
        "rows": num_rows,
        "messages_published": messages_published,
        "topic": settings.kafka_topic,
        "status": "published",
    }
