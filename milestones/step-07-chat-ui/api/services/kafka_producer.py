"""
api/services/kafka_producer.py
--------------------------------
GraphChatEngine – Kafka Producer Service

Milestone 03: Kafka Producer

Responsibilities:
  1. Connect to Kafka broker (with retry on failure)
  2. Serialize each CSV row as a structured JSON message
  3. Publish messages to the configured topic one-by-one
  4. Flush and close the producer gracefully
  5. Return a publish summary (messages_published, topic)

Message format per row:
  {
      "job_id":     "<uuid>",
      "row_number": 1,
      "timestamp":  "2026-07-30T12:00:00.000000",
      "data":       { ...row fields... }
  }

STOP CONDITION — Milestone 03:
  This service publishes rows to Kafka.
  It does NOT consume messages (Milestone 04).
  It does NOT write to Neo4j (Milestone 04).
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from api.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class KafkaPublishError(Exception):
    """
    Raised when the Kafka producer cannot connect or publish a message.

    Attributes
    ----------
    message : str
        Human-readable error description returned to the HTTP layer.
    http_status : int
        Suggested HTTP status code for the response.
    """

    def __init__(self, message: str, http_status: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status


# ---------------------------------------------------------------------------
# Producer factory
# ---------------------------------------------------------------------------

def _build_producer() -> KafkaProducer:
    """
    Create and return a connected KafkaProducer instance.

    Configuration:
    - bootstrap_servers   : read from KAFKA_BOOTSTRAP_SERVERS env var
    - value_serializer    : serialize Python dicts to UTF-8 JSON bytes
    - key_serializer      : serialize string keys to UTF-8 bytes
    - acks='all'          : wait for all in-sync replicas to acknowledge
    - retries=3           : retry up to 3 times on transient failures
    - max_block_ms=10000  : block at most 10 s when buffer is full
    - request_timeout_ms  : 15 s per request

    Raises
    ------
    KafkaPublishError
        If no broker is reachable within the connection timeout.
    """
    try:
        logger.info(
            "Connecting to Kafka | bootstrap_servers=%s",
            settings.kafka_bootstrap_servers,
        )
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            # Serialize dict → JSON bytes
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            # Serialize job_id string → bytes (used as partition key)
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            # Durability: wait for all in-sync replicas to acknowledge
            acks="all",
            # Retry transient broker errors up to 3 times
            retries=3,
            # Block at most 10 s when the internal send buffer is full
            max_block_ms=10_000,
            # Individual request timeout
            request_timeout_ms=15_000,
            # How long to retry on retriable errors (ms)
            retry_backoff_ms=500,
        )
        logger.info("Kafka connected | topic=%s", settings.kafka_topic)
        return producer

    except NoBrokersAvailable as exc:
        logger.error(
            "Kafka unavailable | bootstrap_servers=%s | error=%s",
            settings.kafka_bootstrap_servers,
            str(exc),
        )
        raise KafkaPublishError(
            message=(
                f"Kafka broker is not available at '{settings.kafka_bootstrap_servers}'. "
                "Ensure the Kafka service is running and healthy."
            ),
            http_status=503,
        ) from exc

    except Exception as exc:
        logger.error("Unexpected Kafka connection error | error=%s", str(exc), exc_info=True)
        raise KafkaPublishError(
            message=f"Failed to connect to Kafka: {exc}",
            http_status=503,
        ) from exc


# ---------------------------------------------------------------------------
# Row serialization helper
# ---------------------------------------------------------------------------

def _build_message(job_id: str, row_number: int, row_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a single Kafka message payload for one CSV row.

    Parameters
    ----------
    job_id : str
        UUID4 identifier shared across all messages in this upload.
    row_number : int
        1-based index of the row within the CSV file.
    row_data : dict
        The row's column→value mapping (produced by DataFrame.to_dict()).

    Returns
    -------
    dict
        Structured message matching the agreed format:
        {job_id, row_number, timestamp, data}
    """
    return {
        "job_id": job_id,
        "row_number": row_number,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "data": row_data,
    }


# ---------------------------------------------------------------------------
# Main publish function
# ---------------------------------------------------------------------------

def publish_rows_to_kafka(
    job_id: str,
    rows: List[Dict[str, Any]],
    topic: str,
) -> int:
    """
    Publish a list of CSV row dicts to a Kafka topic.

    Each row is sent as a separate Kafka message with the job_id as the
    partition key (ensuring all rows from the same job land on the same
    partition and are consumed in order).

    Parameters
    ----------
    job_id : str
        UUID4 identifier for this ingest job (used as Kafka message key).
    rows : list of dict
        Each element is one CSV row as a column→value mapping.
    topic : str
        Kafka topic name to publish to.

    Returns
    -------
    int
        Number of messages successfully published.

    Raises
    ------
    KafkaPublishError
        If connection fails or any message cannot be published.
    """
    producer: KafkaProducer = _build_producer()
    messages_published: int = 0

    try:
        logger.info(
            "Publishing started | job_id=%s | total_rows=%d | topic=%s",
            job_id,
            len(rows),
            topic,
        )

        for row_number, row_data in enumerate(rows, start=1):
            message = _build_message(job_id, row_number, row_data)

            logger.debug("Publishing row %d | job_id=%s", row_number, job_id)

            try:
                # send() is asynchronous — it queues the message internally.
                # We pass the job_id as the key so all rows from one upload
                # go to the same partition (ordered delivery).
                future = producer.send(
                    topic=topic,
                    key=job_id,
                    value=message,
                )
                # Block on this individual future to catch per-message errors.
                # For high-throughput scenarios, batch the futures and check
                # them after the loop — but for correctness, we validate each.
                future.get(timeout=10)
                messages_published += 1

                logger.debug(
                    "Published row %d | job_id=%s | messages_published=%d",
                    row_number,
                    job_id,
                    messages_published,
                )

            except KafkaError as exc:
                logger.error(
                    "Publish failed | row=%d | job_id=%s | error=%s",
                    row_number,
                    job_id,
                    str(exc),
                )
                raise KafkaPublishError(
                    message=f"Failed to publish row {row_number} to Kafka: {exc}",
                    http_status=500,
                ) from exc

        # Flush ensures all buffered messages are actually sent to the broker
        # before we return. Without flush(), the producer might exit before
        # the last messages are transmitted.
        producer.flush(timeout=30)

        logger.info(
            "Publish complete | job_id=%s | messages_published=%d | topic=%s",
            job_id,
            messages_published,
            topic,
        )
        return messages_published

    except KafkaPublishError:
        # Re-raise our typed errors without wrapping
        raise

    except Exception as exc:
        logger.error(
            "Unexpected error during Kafka publish | job_id=%s | error=%s",
            job_id,
            str(exc),
            exc_info=True,
        )
        raise KafkaPublishError(
            message=f"An unexpected error occurred while publishing to Kafka: {exc}",
            http_status=500,
        ) from exc

    finally:
        # Always close the producer to release broker connections and
        # internal threads, regardless of success or failure.
        try:
            producer.close(timeout=10)
            logger.info("Kafka producer closed | job_id=%s", job_id)
        except Exception as close_exc:
            logger.warning(
                "Error closing Kafka producer | job_id=%s | error=%s",
                job_id,
                str(close_exc),
            )
