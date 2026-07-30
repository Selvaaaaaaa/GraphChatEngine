"""
api/core/logging_config.py
--------------------------
GraphChatEngine – Centralised Logging Setup

Call configure_logging() once at application startup.
All modules obtain their logger via:

    import logging
    logger = logging.getLogger(__name__)
"""

import logging
import sys

from api.core.config import settings


def configure_logging() -> None:
    """
    Configure the root logger with a consistent format.

    Log level is driven by the LOG_LEVEL environment variable
    (defaulting to INFO). Logs are written to stdout so Docker
    can capture them with `docker compose logs`.
    """
    level = getattr(logging, settings.log_level, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
