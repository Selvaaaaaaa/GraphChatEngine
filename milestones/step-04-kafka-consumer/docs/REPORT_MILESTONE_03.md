# REPORT NOTES – Milestone 03: Kafka Producer

> Ready-to-copy sections for the project report. Covers the Kafka producer implementation, architecture, challenges, and testing.

---

## Objective

Milestone 03 extends the existing `POST /ingest` endpoint to complete the **CSV → Kafka** segment of the data pipeline. After a CSV file passes all validation checks (implemented in Milestone 02), every row is now published as an individual JSON-structured Kafka message to the `customer-data` topic.

The Kafka producer is implemented as a dedicated service module (`api/services/kafka_producer.py`), following the same clean architecture pattern established in Milestones 01 and 02. The HTTP router remains free of any Kafka code.

---

## Architecture

### Updated Data Flow

```
User → POST /ingest (CSV file)
         │
         ▼
  [ingest_service.py]
    1. Validate file extension
    2. Parse with pandas
    3. Structural validation
    4. Generate job_id (UUID4)
    5. Convert DataFrame → list of dicts
         │
         ▼
  [kafka_producer.py]   ← NEW in Milestone 03
    6. Connect to Kafka broker (with retry on failure)
    7. For each row:
         - Build message envelope {job_id, row_number, timestamp, data}
         - Produce to topic: customer-data
         - Await acknowledgement (acks=all)
    8. Flush producer (wait for all buffered sends)
    9. Close producer (release connections)
         │
         ▼
  Return HTTP 200:
  {job_id, filename, rows, messages_published, topic, status="published"}
```

### Module Responsibilities

| Module                         | Responsibility                                        |
|--------------------------------|-------------------------------------------------------|
| `routers/ingest.py`            | Parse HTTP request; map results/errors to responses   |
| `services/ingest_service.py`   | Orchestrate: validate → convert → call producer       |
| `services/kafka_producer.py`   | Connect to Kafka; build messages; publish; flush; close|
| `core/config.py`               | Read `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_TOPIC` from env|
| `schemas/ingest.py`            | `IngestPublishedResponse` — new Milestone 03 schema   |

---

## Technologies Used

| Technology     | Version  | Role in Milestone 03                                        |
|----------------|----------|-------------------------------------------------------------|
| kafka-python   | 2.0.2    | Python Kafka client library; `KafkaProducer` class          |
| Apache Kafka   | 3.7.0    | Message broker receiving CSV row messages                   |
| pandas         | 2.2.2    | `DataFrame.to_dict(orient='records')` — row serialisation   |
| FastAPI        | 0.111.0  | HTTP layer unchanged; new `IngestPublishedResponse` schema  |
| Pydantic       | 2.x      | `IngestPublishedResponse` model drives Swagger + validation |

---

## Kafka Producer Configuration

```python
KafkaProducer(
    bootstrap_servers="kafka:29092",
    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
    acks="all",          # Wait for all in-sync replicas
    retries=3,           # Retry on transient broker errors
    max_block_ms=10_000, # Block at most 10s when buffer is full
    request_timeout_ms=15_000,
    retry_backoff_ms=500,
)
```

| Parameter           | Value    | Rationale                                                |
|---------------------|----------|----------------------------------------------------------|
| `acks="all"`        | all      | Maximum durability — no message loss                     |
| `retries`           | 3        | Handles transient leader elections and network blips     |
| `max_block_ms`      | 10,000   | Fail fast if buffer fills; don't block HTTP indefinitely |
| `request_timeout_ms`| 15,000   | Per-request timeout; raises after 15s with no response   |

---

## Message Format

Each Kafka message carries a structured envelope:

```json
{
  "job_id":     "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "row_number": 1,
  "timestamp":  "2026-07-30T12:53:00.123456",
  "data": {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice.johnson@example.com",
    "age": 29,
    "city": "New York",
    "country": "USA"
  }
}
```

**Design rationale:**
- `job_id` as message key → all rows from one upload land in the same partition (ordered delivery)
- `row_number` → consumer can detect missing messages and maintain insertion order
- `timestamp` → event time for stream processing and latency monitoring
- `data` → isolated payload; consumer extracts this without parsing the envelope

---

## Challenges

### Challenge 1: pandas NaN Serialisation

**Problem:** pandas represents missing CSV values (empty cells) as `float('nan')`. Python's `json.dumps()` serialises `NaN` as the literal string `NaN`, which is **not valid JSON** — JSON only supports `null` for missing values.

**Solution:** Replace NaN values with Python `None` before converting to dicts:
```python
rows_as_dicts = dataframe.where(pd.notnull(dataframe), None).to_dict(orient="records")
```
`None` serialises as `null` in JSON, which is valid.

---

### Challenge 2: Graceful Kafka Unavailability

**Problem:** If the Kafka container is restarting or temporarily unavailable, `KafkaProducer()` raises `NoBrokersAvailable` immediately. This must not crash the API — it must return a meaningful HTTP error.

**Solution:** Catch `NoBrokersAvailable` in `_build_producer()` and convert it to a `KafkaPublishError` with `http_status=503`. The router catches `KafkaPublishError` specifically and returns:
```json
HTTP 503
{"error": "Kafka broker is not available at 'kafka:29092'. Ensure the Kafka service is running."}
```

---

### Challenge 3: Producer Lifecycle Management

**Problem:** `KafkaProducer.send()` is asynchronous — it buffers messages internally. Simply returning after the loop might not guarantee delivery of the last messages.

**Solution:** Two-step shutdown:
1. `producer.flush(timeout=30)` — blocks until all buffered messages are acknowledged
2. `producer.close(timeout=10)` in a `finally` block — always closes connections, even on failure

---

## API Response

**Before (Milestone 02):**
```json
{
  "job_id": "...",
  "filename": "customers.csv",
  "rows": 15,
  "columns": 8,
  "column_names": ["id", "name", ...],
  "size_kb": 1.12,
  "status": "validated",
  "timestamp": "2026-07-30T..."
}
```

**After (Milestone 03):**
```json
{
  "job_id": "...",
  "filename": "customers.csv",
  "rows": 15,
  "messages_published": 15,
  "topic": "customer-data",
  "status": "published"
}
```

The response is simpler and pipeline-focused — it confirms delivery rather than describing the file.

---

## Testing

### Test Commands

```bash
# Upload customers.csv — expect HTTP 200, 15 messages
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"

# Upload employees.csv — expect HTTP 200, 15 messages
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/employees.csv"

# Verify messages reached Kafka
docker exec graphchat-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customer-data \
  --from-beginning \
  --max-messages 15
```

### Test Results

| Test                              | Expected                | Result |
|-----------------------------------|-------------------------|--------|
| Upload `customers.csv` (15 rows)  | HTTP 200, published: 15 | ✅ Pass |
| Upload `employees.csv` (15 rows)  | HTTP 200, published: 15 | ✅ Pass |
| Upload `products.csv` (15 rows)   | HTTP 200, published: 15 | ✅ Pass |
| Upload `orders.csv` (15 rows)     | HTTP 200, published: 15 | ✅ Pass |
| Upload `invalid.txt`              | HTTP 400 (extension)    | ✅ Pass |
| Upload `empty.csv`                | HTTP 400 (no rows)      | ✅ Pass |
| Kafka consumer shows 15 messages  | 15 JSON lines printed   | ✅ Pass |
| API logs show all publish steps   | Log lines present       | ✅ Pass |

---

## Screenshots to Capture

1. **POST /ingest — Milestone 03 success response** — `{"status":"published","messages_published":15,...}`
2. **Kafka consumer output** — 15 JSON messages after `kafka-console-consumer.sh --from-beginning`
3. **Swagger UI** — Updated endpoint description showing "publish rows to Kafka"
4. **API logs** — `docker compose logs api` showing `Kafka connected`, `Published row X`, `Pipeline complete`
5. **Kafka topic describe** — `kafka-topics.sh --describe --topic customer-data` showing partition info
6. **docker ps** — All containers `(healthy)`, including api

---

## Advantages of Kafka in This Pipeline

| Advantage         | Explanation                                                                         |
|-------------------|-------------------------------------------------------------------------------------|
| **Decoupling**    | API and Loader are independent — Loader can be restarted without affecting the API  |
| **Durability**    | Messages persist on disk — if Loader crashes, no data is lost; replay from offset   |
| **Scalability**   | Add more Loader instances; Kafka distributes partitions across consumers automatically |
| **Backpressure**  | Loader processes at its own pace — slow Neo4j writes don't slow CSV uploads          |
| **Replayability** | Re-process historical CSV data by resetting consumer offset to 0                    |
| **Ordering**      | job_id as key ensures all rows from one upload are consumed in insertion order       |

---

## Limitations

| Limitation                         | Description                                               |
|------------------------------------|-----------------------------------------------------------|
| No idempotency                     | Re-uploading the same CSV produces duplicate messages     |
| No consumer yet                    | Messages queue in Kafka; Neo4j graph is still empty       |
| Single-partition topic             | Auto-created with 1 partition — no parallelism            |
| No schema registry                 | Message schema is enforced by convention, not Avro/Protobuf |
| No dead-letter queue               | Failed publishes cause the entire upload to fail (no retry per-message) |

---

## Future Work

| Milestone | Feature                                            |
|-----------|----------------------------------------------------|
| 04        | Kafka consumer in Loader — read `customer-data`   |
| 04        | Neo4j Cypher MERGE — create nodes from messages   |
| 04        | Consumer group offset management                  |
| 05        | Chatbot queries against populated Neo4j graph     |
| Future    | Kafka topic schema via Avro + Schema Registry     |
| Future    | Dead-letter topic for failed consumer messages    |
| Future    | Idempotent producer (`enable.idempotence=True`)   |
