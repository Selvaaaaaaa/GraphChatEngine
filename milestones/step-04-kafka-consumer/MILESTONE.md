# Milestone 04 – Kafka Consumer

## Objective

Implement a standalone, resilient Kafka Consumer service in the `loader` container (`loader/services/kafka_consumer.py` and `loader/consumer.py`) that continuously consumes messages from the `customer-data` Kafka topic, deserializes JSON payloads, validates schema structure, logs event output, and buffers valid messages in memory.

---

## Features Completed

- ✅ **`loader/services/kafka_consumer.py`** — Service layer managing Kafka connection, polling, validation, logging, and in-memory storage.
- ✅ **`loader/consumer.py`** — Execution entrypoint handling process startup and OS signal termination (`SIGINT`/`SIGTERM`).
- ✅ **`loader/loader.py`** — Updated entrypoint delegating to `consumer.py`.
- ✅ **`loader/requirements.txt`** — Added `kafka-python==2.0.2`.
- ✅ **`loader/Dockerfile`** — Updated with `PYTHONPATH=/app` and `CMD ["python", "consumer.py"]`.
- ✅ **`docker-compose.yml`** — Updated loader environment variables (`KAFKA_TOPIC`, `GROUP_ID`, `AUTO_OFFSET_RESET`).
- ✅ **`.env.example`** — Added `GROUP_ID` and `AUTO_OFFSET_RESET` configuration docs.
- ✅ **`docs/VIVA_MILESTONE_04.md`** — 20 professional viva Q&As.
- ✅ **`docs/REPORT_MILESTONE_04.md`** — Complete milestone report.
- ✅ **`README.md`** — Updated with Kafka Consumer section, workflow, configuration, and testing guide.

---

## What Works

| Feature | Status | Notes |
|---------|--------|-------|
| Kafka Connection & Auto-Retry | ✅ | Retries with backoff if Kafka is unavailable |
| Topic Subscription | ✅ | Subscribes to `customer-data` |
| JSON Deserialization | ✅ | Safely deserializes binary payload |
| Message Schema Validation | ✅ | Validates `job_id`, `row_number`, `timestamp`, `data` |
| Malformed Message Rejection | ✅ | Skips invalid messages without crashing |
| Live Ingestion & Logging | ✅ | Prints `Received row X | job_id=...` |
| In-Memory Buffer Storage | ✅ | Stores validated messages in `memory_store` |
| Signal Handling & Graceful Stop | ✅ | Closes Kafka consumer connection cleanly on SIGTERM |

---

## What Does NOT Work Yet (By Design)

| Feature | Target Milestone |
|---------|------------------|
| Neo4j Cypher Database Insertion | Milestone 05 |
| Graph Relationship Building | Milestone 05 |
| Chatbot NLP Interface | Milestone 06 |

---

## Consumer Log Output Example

```text
2026-07-30T13:15:20 | INFO     | loader.kafka_consumer | Received Message | Job ID: 12588210-9a39-4710-a8ee-dfe86c7872dc | Row Number: 1 | timestamp: 2026-07-30T13:15:20.088318
Received row 1 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
Received row 2 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
...
Received row 15 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
```
