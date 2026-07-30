"""
api/core/config.py
------------------
GraphChatEngine – Centralised Application Configuration

Reads environment variables once at startup and exposes them as
a typed Settings object. All other modules import from here — never
from os.environ directly.
"""

import os


class Settings:
    """
    Application settings loaded from environment variables.

    Attributes
    ----------
    app_env : str
        Deployment environment (development | staging | production).
    log_level : str
        Python logging level string.
    max_upload_size_mb : int
        Maximum allowed CSV upload size in megabytes.
    allowed_content_types : set[str]
        MIME types accepted for CSV uploads.
    """

    # Application
    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "info").upper()

    # Upload limits
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

    # Accepted MIME types for CSV files
    allowed_content_types: set = {
        "text/csv",
        "text/plain",           # Some browsers send text/plain for .csv
        "application/csv",
        "application/octet-stream",  # Generic binary — extension check is primary guard
    }

    # Kafka — active from Milestone 03
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "customer-data")

    # Neo4j (not used until Milestone 04)
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "changeme")


# Singleton instance — import this everywhere
settings = Settings()
