# REPORT NOTES – Milestone 04: Kafka Consumer

> Comprehensive documentation for Milestone 04 covering Kafka Consumer architecture, workflow, implementation details, testing verification, and future scope.

---

## Objective

The objective of Milestone 04 was to implement a robust, resilient **Kafka Consumer** service inside the `loader` worker container (`loader/services/kafka_consumer.py` and `loader/consumer.py`).

The consumer continuously subscribes to the `customer-data` topic on Apache Kafka, receives JSON-encoded row messages produced by the API, deserializes and validates their schema, logs reception details, and stores valid messages temporarily in process memory.

Per milestone boundaries:
- **Included:** Kafka consumption, JSON deserialization, schema validation, structured logging, in-memory storage, graceful signal handling.
- **Excluded:** Neo4j graph database insertion (reserved for Milestone 05).

---

## Architecture & Data Flow

```
┌─────────────────┐       ┌─────────────────┐       ┌────────────────────────┐
│   FastAPI API   │ ────► │  Kafka Broker   │ ────► │ Loader Consumer        │
│ (POST /ingest)  │       │ (customer-data) │       │ (loader/consumer.py)   │
└─────────────────┘       └─────────────────┘       └───────────┬────────────┘
                                                                │
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │ Deserialize JSON       │
                                                    └───────────┬────────────┘
                                                                │
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │ Validate Schema        │
                                                    │ (job_id, row, ts, data)│
                                                    └───────────┬────────────┘
                                                                │
                                              ┌─────────────────┴────────────────┐
                                              │                                  │
                                       [Valid Message]                  [Invalid Message]
                                              │                                  │
                                              ▼                                  ▼
                                    ┌──────────────────┐               ┌──────────────────┐
                                    │ Log Received Row │               │ Log Error & Skip │
                                    │ Store in Memory  │               │ (Never Crash)    │
                                    └──────────────────┘               └──────────────────┘
```

---

## Consumer Workflow

1. **Initialization:** `consumer.py` initializes `IngestConsumerService` and registers OS signal handlers (`SIGINT`, `SIGTERM`).
2. **Connection & Retry:** `connect_consumer()` connects to Kafka (`kafka:29092`) using `GROUP_ID` (`graphchat-loader-group`) and `AUTO_OFFSET_RESET` (`earliest`). If Kafka is initializing, it retries with backoff.
3. **Topic Subscription:** Subscribes to `customer-data` topic.
4. **Poll Loop:** Continuously polls Kafka using `consumer.poll(timeout_ms=1000)`.
5. **Deserialization & Validation:**
   - Deserializes binary payload to JSON dict.
   - Validates existence of `job_id`, `row_number`, `timestamp`, and `data`.
6. **Processing & Logging:**
   - Logs `Received Message | Job ID: ... | Row Number: X`.
   - Prints `Received row X | job_id=...`.
   - Appends message to `self.memory_store`.
7. **Shutdown:** On container stop, closes Kafka consumer connection cleanly (`LeaveGroup`).

---

## Consumer Configuration

| Configuration Var | Value | Description |
|-------------------|-------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka broker internal bootstrap address |
| `KAFKA_TOPIC` | `customer-data` | Target Kafka topic name |
| `GROUP_ID` | `graphchat-loader-group` | Consumer group identifier |
| `AUTO_OFFSET_RESET` | `earliest` | Reads all topic messages from beginning |

---

## Verification & Expected Output

### Test Command
```bash
# Upload a CSV file via API
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```

### API Response
```json
{
  "job_id": "12588210-9a39-4710-a8ee-dfe86c7872dc",
  "filename": "customers.csv",
  "rows": 15,
  "messages_published": 15,
  "topic": "customer-data",
  "status": "published"
}
```

### Loader Container Log Output
```text
2026-07-30T13:15:20 | INFO     | loader.kafka_consumer | Received Message | Job ID: 12588210-9a39-4710-a8ee-dfe86c7872dc | Row Number: 1 | timestamp: 2026-07-30T13:15:20.088318
Received row 1 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
2026-07-30T13:15:20 | INFO     | loader.kafka_consumer | Received Message | Job ID: 12588210-9a39-4710-a8ee-dfe86c7872dc | Row Number: 2 | timestamp: 2026-07-30T13:15:20.099121
Received row 2 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
...
Received row 15 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
```

---

## Screenshots to Capture

1. **`docker compose logs loader`** showing real-time consumption of CSV rows (`Received row 1`, `Received row 2`, etc.).
2. **`docker ps`** displaying `graphchat-loader` container in `Up` status alongside `graphchat-api`, `graphchat-kafka`, and `graphchat-neo4j`.
3. **Terminal curl upload** showing `POST /ingest` returning HTTP 200 with `status: "published"`.
4. **Kafka consumer log initialization** showing `Consumer Started`, `Kafka Connected`, `Subscribed Topic`.

---

## Future Scope (Milestone 05+)

- **Neo4j Cypher Ingestion:** Connect `IngestConsumerService` to a Neo4j Writer module that translates message `data` payloads into `MERGE` Cypher queries to build nodes (`:Customer`, `:Order`, `:Product`) and relationships (`:PLACED`, `:CONTAINS`).
- **Manual Offset Commit:** Move from auto-commit to committing Kafka offsets only after successful Neo4j database transactions.
- **Dead-Letter Queue (DLQ):** Route invalid or unparseable messages to a `customer-data-dlq` topic for audit and reprocessing.
