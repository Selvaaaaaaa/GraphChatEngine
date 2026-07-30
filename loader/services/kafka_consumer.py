"""
loader/services/kafka_consumer.py
----------------------------------
GraphChatEngine – Kafka Consumer Service

Milestone 04: Kafka Consumer

Responsibilities:
  1. Read configuration from environment variables (KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, GROUP_ID, AUTO_OFFSET_RESET)
  2. Connect to Kafka broker with automatic retry/reconnection
  3. Subscribe to the configured topic ("customer-data")
  4. Continuously poll and receive JSON messages
  5. Validate message structure (job_id, row_number, timestamp, data)
  6. Reject malformed messages without crashing
  7. Log all events (Consumer Started, Kafka Connected, Subscribed Topic, Received Message, Row Number, Job ID, Consumer Waiting, Errors, Consumer Shutdown)
  8. Store valid messages temporarily in memory
  9. Support graceful shutdown

STOP CONDITION — Milestone 04:
  Receives and validates Kafka messages and stores them in memory.
  Does NOT insert into Neo4j (Milestone 05).
"""

import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable

from services.graph_loader import GraphLoader

# Set up logging for loader service
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("loader.kafka_consumer")


class IngestConsumerService:
    """
    Kafka Consumer Service for GraphChatEngine Ingest Pipeline.
    """

    def __init__(self) -> None:
        # Load configuration from environment variables
        self.bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
        self.topic: str = os.getenv("KAFKA_TOPIC", "customer-data")
        self.group_id: str = os.getenv("GROUP_ID", "graphchat-loader-group")
        self.auto_offset_reset: str = os.getenv("AUTO_OFFSET_RESET", "earliest")

        # In-memory storage for validated messages
        self.memory_store: List[Dict[str, Any]] = []

        self.consumer: Optional[KafkaConsumer] = None
        self.running: bool = False

        # Initialize Graph Loader service
        self.graph_loader: GraphLoader = GraphLoader()

    def connect_consumer(self) -> KafkaConsumer:
        """
        Attempt to create and connect a KafkaConsumer with retry logic.
        """
        retry_delay = 2
        max_delay = 30

        while True:
            try:
                logger.info(
                    "Kafka Connecting | bootstrap_servers=%s | group_id=%s | topic=%s",
                    self.bootstrap_servers,
                    self.group_id,
                    self.topic,
                )
                consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    auto_offset_reset=self.auto_offset_reset,
                    enable_auto_commit=True,
                    auto_commit_interval_ms=1000,
                    value_deserializer=lambda m: self._deserialize_value(m),
                    consumer_timeout_ms=1000,  # 1s poll timeout to allow checking self.running flag
                )
                logger.info("Kafka Connected | bootstrap_servers=%s", self.bootstrap_servers)
                logger.info("Subscribed Topic | topic=%s", self.topic)
                return consumer
            except NoBrokersAvailable as exc:
                logger.warning(
                    "Kafka unavailable | error=%s | Retrying in %ds...",
                    str(exc),
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            except Exception as exc:
                logger.error("Error connecting to Kafka | error=%s | Retrying in %ds...", str(exc), retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    def _deserialize_value(self, payload: bytes) -> Optional[Dict[str, Any]]:
        """
        Safely deserialize raw bytes to a Python dictionary.
        """
        if not payload:
            return None
        try:
            return json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.error("Malformed JSON deserialization error | error=%s", str(exc))
            return None

    def validate_message(self, message_val: Any) -> bool:
        """
        Validate required fields in the message dictionary.
        Required fields: job_id, row_number, timestamp, data.
        """
        if not isinstance(message_val, dict):
            logger.error("Validation Error | Payload is not a dictionary | payload=%s", str(message_val))
            return False

        required_fields = ["job_id", "row_number", "timestamp", "data"]
        missing_fields = [field for field in required_fields if field not in message_val or message_val[field] is None]

        if missing_fields:
            logger.error(
                "Validation Error | Missing required fields: %s | payload=%s",
                missing_fields,
                json.dumps(message_val, default=str),
            )
            return False

        return True

    def process_message(self, message_val: Dict[str, Any]) -> None:
        """
        Process, validate, log, and temporarily store a message in memory.
        """
        if not self.validate_message(message_val):
            logger.warning("Rejected malformed or incomplete message.")
            return

        job_id = message_val["job_id"]
        row_number = message_val["row_number"]
        timestamp = message_val["timestamp"]
        data = message_val["data"]

        # Formatted logging block for verification review
        logger.info(
            "\n------------------------------------------------\n"
            "Received Message\n"
            "Job ID         : %s\n"
            "Row Number     : %d\n"
            "Topic          : %s\n"
            "Consumer Group : %s\n"
            "Status         : SUCCESS\n"
            "------------------------------------------------",
            job_id,
            row_number,
            self.topic,
            self.group_id,
        )
        # Standard stdout log format:
        print(f"Received row {row_number} | job_id={job_id}", flush=True)

        # Store temporarily in memory
        self.memory_store.append(message_val)
        logger.debug("Stored message in memory | Total in memory: %d", len(self.memory_store))

        # Pass data to Graph Loader service for Neo4j insertion
        try:
            self.graph_loader.process_record(data)
        except Exception as exc:
            logger.error("Error delegating record to GraphLoader | error=%s", str(exc))

    def start(self) -> None:
        """
        Start the Kafka consumer loop.
        """
        logger.info("Consumer Started")
        self.running = True
        self.consumer = self.connect_consumer()

        logger.info("Consumer Waiting for messages...")

        idle_counter = 0

        while self.running:
            try:
                # Poll for messages
                records = self.consumer.poll(timeout_ms=1000)

                if not records:
                    idle_counter += 1
                    if idle_counter % 30 == 0:  # Log periodically while waiting
                        logger.info("Consumer Waiting | topic=%s | Total stored in memory: %d", self.topic, len(self.memory_store))
                    continue

                idle_counter = 0

                for topic_partition, consumer_records in records.items():
                    for record in consumer_records:
                        if not self.running:
                            break
                        if record.value is None:
                            logger.warning("Skipping empty or unparseable record at offset %d", record.offset)
                            continue

                        self.process_message(record.value)

            except KafkaError as exc:
                logger.error("Kafka consumer error encountered during poll | error=%s", str(exc))
                # Reconnect if consumer connection was interrupted
                time.sleep(2)
                if self.running:
                    self.consumer = self.connect_consumer()
            except Exception as exc:
                logger.error("Unexpected error in consumer loop | error=%s", str(exc), exc_info=True)
                time.sleep(1)

        self.stop()

    def stop(self) -> None:
        """
        Gracefully stop the consumer.
        """
        logger.info("Consumer Shutdown sequence initiated...")
        self.running = False
        if self.consumer:
            try:
                self.consumer.close(timeout=5)
                logger.info("Kafka consumer connection closed.")
            except Exception as exc:
                logger.warning("Error closing Kafka consumer | error=%s", str(exc))

        if self.graph_loader:
            try:
                self.graph_loader.close()
            except Exception as exc:
                logger.warning("Error closing GraphLoader | error=%s", str(exc))

        logger.info("Consumer Shutdown complete.")
