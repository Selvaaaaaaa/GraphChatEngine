"""
loader/loader.py
----------------
GraphChatEngine – Loader Service
Long-running Python process that will eventually:
  1. Watch for uploaded CSV files
  2. Parse and produce records to Kafka
  3. Consume from Kafka and write to Neo4j

Milestone 01: Project Foundation
- Prints a startup banner and keeps the process alive.
- No Kafka, Neo4j, or CSV logic in this milestone.
"""

import time
import signal
import sys


# ---------------------------------------------------------------------------
# Graceful shutdown handler
# ---------------------------------------------------------------------------

def _handle_signal(sig, frame) -> None:  # noqa: ANN001
    """Handle SIGTERM / SIGINT so Docker can stop the container cleanly."""
    print("Loader shutting down gracefully...", flush=True)
    sys.exit(0)


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the loader service and keep it alive."""
    print("Loader Started...", flush=True)
    print("Waiting for work (CSV ingestion pipeline not yet implemented).", flush=True)

    # Keep the process alive; future milestones will replace this loop
    # with actual Kafka consumer / Neo4j writer logic.
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
