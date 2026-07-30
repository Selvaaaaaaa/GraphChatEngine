# Milestone 03 – Kafka Producer

## Objective

Extend the existing `POST /ingest` endpoint to publish each validated CSV row as an individual JSON message to the `customer-data` Kafka topic. This completes the **CSV → Kafka** segment of the pipeline.

---

## Features Completed

- ✅ **`api/services/kafka_producer.py`** — New dedicated Kafka producer service
- ✅ **`api/services/ingest_service.py`** — Extended with Kafka publish step after validation
- ✅ **`api/schemas/ingest.py`** — New `IngestPublishedResponse` schema (`status: published`)
- ✅ **`api/routers/ingest.py`** — Handles `KafkaPublishError` → HTTP 503; uses new response model
- ✅ **`api/core/config.py`** — Added `kafka_topic` setting (`KAFKA_TOPIC` env var)
- ✅ **`api/requirements.txt`** — Activated `kafka-python==2.0.2`
- ✅ **`docker-compose.yml`** — Added `KAFKA_TOPIC` env var to API service
- ✅ **`.env.example`** — Added `KAFKA_TOPIC` with documentation
- ✅ **`docs/VIVA_MILESTONE_03.md`** — 20 professional viva Q&As
- ✅ **`docs/REPORT_MILESTONE_03.md`** — Copy-ready report content

---

## What Works

| Feature                                         | Status | Notes                                          |
|-------------------------------------------------|--------|------------------------------------------------|
| `POST /ingest` validates CSV                    | ✅     | All M02 validation preserved                   |
| `POST /ingest` publishes rows to Kafka          | ✅     | One message per row                            |
| Response shows `messages_published` and `topic` | ✅     | `status: "published"`                          |
| Wrong extension still returns HTTP 400          | ✅     | Validation runs before Kafka                   |
| Kafka unavailable returns HTTP 503              | ✅     | `NoBrokersAvailable` → `KafkaPublishError`     |
| Messages verify with `kafka-console-consumer`   | ✅     | 15 JSON messages per CSV                       |
| API container stays `(healthy)`                 | ✅     | Python urllib health check unchanged           |
| `api/services/kafka_producer.py` is standalone  | ✅     | No Kafka code in router or ingest_service      |

---

## What Does NOT Work Yet

| Feature                    | Planned Milestone |
|----------------------------|-------------------|
| Kafka consumer (Loader)    | Milestone 04      |
| Neo4j graph writes         | Milestone 04      |
| Cypher queries             | Milestone 04      |
| Chatbot interface          | Milestone 05      |
| UI upload form             | Milestone 04      |
| Job status tracking        | Milestone 04      |

---

## Kafka Message Format

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
    "country": "USA",
    "joined_date": "2022-03-15",
    "tier": "gold"
  }
}
```

---

## API Response (Milestone 03)

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "customers.csv",
  "rows": 15,
  "messages_published": 15,
  "topic": "customer-data",
  "status": "published"
}
```

---

## New File: `api/services/kafka_producer.py`

```
_build_producer()         → Creates KafkaProducer with config (acks=all, retries=3)
_build_message()          → Assembles {job_id, row_number, timestamp, data} envelope
publish_rows_to_kafka()   → Loop: build → send → future.get() → flush → close
KafkaPublishError         → Typed exception (message + http_status)
```

---

## Pipeline Architecture

```
POST /ingest
     │
     ▼
ingest_service.py
  1. Validate CSV (extension, parse, structure)
  2. Generate job_id
  3. Convert DataFrame → list of row dicts (NaN → None)
     │
     ▼
kafka_producer.py  ← NEW
  4. KafkaProducer(bootstrap_servers, acks=all, retries=3)
  5. For each row:
       message = {job_id, row_number, timestamp, data}
       future = producer.send(topic, key=job_id, value=message)
       future.get(timeout=10)
  6. producer.flush(timeout=30)
  7. producer.close(timeout=10)  [finally block]
     │
     ▼
Return HTTP 200:
  {job_id, filename, rows, messages_published, topic, status="published"}
```

---

## Commands

```bash
# Rebuild API with Kafka support
docker compose up --build -d api

# Upload and publish to Kafka
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/employees.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/products.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/orders.csv"

# Verify messages in Kafka
docker exec graphchat-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customer-data \
  --from-beginning \
  --max-messages 60

# Describe the topic
docker exec graphchat-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic customer-data

# View API logs
docker compose logs --tail=50 api

# Error path tests
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.txt"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/empty.csv"
```

---

## Key Design Decisions

### 1. Dedicated service module (`kafka_producer.py`)
Kafka logic is fully isolated in its own module. The router and `ingest_service.py` call it through a clean function signature — no Kafka imports anywhere except `kafka_producer.py`.

### 2. `job_id` as partition key
All rows from one upload go to the same partition, guaranteeing ordered consumption. This is essential for Neo4j writes where row order may matter.

### 3. `acks='all'` for durability
Even in single-broker development setup, `acks='all'` ensures the code works correctly in production without changes.

### 4. `NaN → None` before serialisation
pandas NaN is not valid JSON. Replacing with `None` (→ `null`) before `to_dict()` prevents `ValueError` during JSON serialisation.

### 5. `finally: producer.close()`
Producer is always closed — even on failure. Prevents thread and connection leaks.

---

## Viva Notes

**Q: Where is the Kafka producer code?**
`api/services/kafka_producer.py` — dedicated module. Zero Kafka code in router or ingest_service.

**Q: Why `acks='all'`?**
Wait for all in-sync replicas. Maximum durability — no message loss even on broker failover. In single-broker dev, equivalent to `acks=1`.

**Q: Why `job_id` as message key?**
Kafka hashes the key to assign a partition. Same key → same partition → ordered consumption. All 15 rows of one upload are consumed in the correct sequence.

**Q: What is `producer.flush()`?**
`send()` is async — it buffers messages. `flush()` blocks until all buffered messages are acknowledged. Required before `close()` to guarantee delivery.

**Q: How is `NaN` handled?**
`dataframe.where(pd.notnull(df), None)` replaces `float('nan')` with `None` before `to_dict()`. `None` serialises as JSON `null`. Without this, `json.dumps()` produces invalid JSON `NaN`.

**Q: What happens if Kafka is down?**
`NoBrokersAvailable` is caught in `_build_producer()` → raised as `KafkaPublishError(http_status=503)` → router returns HTTP 503 with descriptive message.

---

## Report Notes

Milestone 03 closes the CSV → Kafka gap, completing the first two stages of the five-stage pipeline. The implementation follows the established clean architecture: the router delegates to `ingest_service.py`, which orchestrates validation and calls `kafka_producer.py` for all Kafka operations.

Key technical decisions:
- **`acks='all'`** — durability over throughput; appropriate for a data pipeline
- **`job_id` as partition key** — ensures ordered delivery, critical for Neo4j graph construction
- **`NaN → None`** — handles pandas' missing value representation before JSON serialisation
- **`finally: producer.close()`** — deterministic resource cleanup regardless of success/failure

The HTTP response shape was redesigned from the Milestone 02 `validated` response to a `published` response that confirms Kafka delivery rather than describing file metadata.
