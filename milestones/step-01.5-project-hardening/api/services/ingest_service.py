"""
api/services/ingest_service.py
-------------------------------
GraphChatEngine – CSV Ingest Service

This module contains all the pure business logic for Milestone 02:
  1. File-type validation (extension + MIME guard)
  2. CSV parsing via pandas
  3. Structural validation (empty file, missing headers, malformed rows)
  4. Metadata extraction (rows, columns, column names, size)
  5. Job ID generation

IMPORTANT – Milestone 02 stop condition:
  This service returns a validated metadata dict.
  It does NOT produce to Kafka (Milestone 03).
  It does NOT write to Neo4j (Milestone 03).
"""

import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

import pandas as pd
from fastapi import UploadFile

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
    Validate and extract metadata from an uploaded CSV file.

    Parameters
    ----------
    file : UploadFile
        The multipart file object provided by FastAPI.

    Returns
    -------
    Dict[str, Any]
        A dictionary matching the IngestSuccessResponse schema:
        {job_id, filename, rows, columns, column_names, size_kb,
         status, timestamp}

    Raises
    ------
    CSVValidationError
        If the file fails any validation check (wrong type, empty,
        missing headers, or unparseable content).
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
    num_columns: int = len(dataframe.columns)
    column_names: list = dataframe.columns.tolist()
    size_kb: float = bytes_to_kb(size_bytes)

    logger.info(
        "Validation success | filename=%s | rows=%d | columns=%d | size_kb=%.2f",
        filename,
        num_rows,
        num_columns,
        size_kb,
    )

    # ------------------------------------------------------------------
    # 6. Generate job metadata
    # ------------------------------------------------------------------
    job_id: str = str(uuid.uuid4())
    timestamp: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

    result: Dict[str, Any] = {
        "job_id": job_id,
        "filename": filename,
        "rows": num_rows,
        "columns": num_columns,
        "column_names": column_names,
        "size_kb": size_kb,
        "status": "validated",
        "timestamp": timestamp,
    }

    logger.info("Job created | job_id=%s | filename=%s", job_id, filename)
    return result
