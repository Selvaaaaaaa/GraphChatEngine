"""
loader/consumer.py
------------------
GraphChatEngine – Kafka Consumer Entrypoint

Milestone 04: Kafka Consumer

Main execution script that initializes and starts the IngestConsumerService.
Handles system signal interrupts (SIGINT, SIGTERM) for graceful container shutdown.
"""

import signal
import sys
from services.kafka_consumer import IngestConsumerService


def main() -> None:
    """
    Main entry point for running the Kafka consumer worker.
    """
    consumer_service = IngestConsumerService()

    def _signal_handler(sig, frame):
        print("\nSignal received, stopping consumer...", flush=True)
        consumer_service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        consumer_service.start()
    except Exception as exc:
        print(f"Consumer terminated with error: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
