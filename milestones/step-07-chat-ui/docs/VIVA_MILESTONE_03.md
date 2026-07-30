# VIVA NOTES – Milestone 03: Kafka Producer

> 20 professional viva questions with detailed answers.
> Covers Kafka architecture, producer API, message design, error handling, serialization, and pipeline design.

---

## Q1. What is Apache Kafka and why is it used in this project?

**Answer:**
Apache Kafka is a distributed event-streaming platform designed for high-throughput, fault-tolerant, ordered delivery of messages between services. It acts as a durable, replayable message bus.

In GraphChatEngine, Kafka decouples the **API** (producer) from the **Loader** (consumer). Without Kafka, the API would need to write directly to Neo4j — creating tight coupling, blocking the HTTP response while Neo4j writes complete, and creating a failure cascade if Neo4j is slow. With Kafka:
- The API returns immediately after publishing (fast HTTP response)
- The Loader processes at its own pace (backpressure handled by Kafka)
- Messages are durable — if the Loader crashes, messages are replayed on restart

---

## Q2. What is the difference between a Kafka topic, partition, and offset?

**Answer:**

| Concept      | Description                                                       |
|--------------|-------------------------------------------------------------------|
| **Topic**    | Named feed/stream of messages (like a database table name). E.g., `customer-data` |
| **Partition**| A topic is split into N ordered, numbered partitions. Each partition is a sequential log. |
| **Offset**   | An integer that uniquely identifies a message's position within a partition. Monotonically increasing. |

In this project, all 15 rows of `customers.csv` go to the `customer-data` topic. Because we use `job_id` as the message key, Kafka hashes the key to assign a partition — ensuring all 15 messages land in the same partition and are consumed in order.

---

## Q3. What does `acks='all'` mean in the Kafka producer?

**Answer:**
`acks` controls how many broker acknowledgements the producer waits for before considering a message "sent":

| Setting    | Meaning                                                    | Risk                  |
|------------|------------------------------------------------------------|-----------------------|
| `acks=0`   | Fire and forget — no wait                                 | Messages can be lost  |
| `acks=1`   | Wait for the leader replica only                          | Lost if leader fails  |
| `acks='all'` | Wait for **all** in-sync replicas to acknowledge         | Safest — no data loss |

For a data pipeline where every CSV row must reach Kafka exactly once, `acks='all'` is the correct choice. In a development setup with a single broker (replication factor 1), `acks='all'` and `acks=1` behave identically — but using `all` ensures the code is production-ready without changes.

---

## Q4. Why is the `job_id` used as the Kafka message key?

**Answer:**
The message key serves two purposes:

1. **Partition routing:** Kafka hashes the key and maps it to a partition number. All messages with the same key always go to the same partition.
2. **Ordering guarantee:** Kafka only guarantees message ordering **within a single partition**. By using `job_id` as the key, all rows from one CSV upload land in the same partition and are consumed in insertion order.

If no key were used, rows from the same CSV could land in different partitions and be consumed out of order — causing Neo4j to receive rows in random sequence, making relationship building harder.

---

## Q5. What is `producer.flush()` and why is it important?

**Answer:**
`KafkaProducer.send()` is **asynchronous** — it places the message in an internal memory buffer and returns a `Future` immediately. The actual network transmission to the broker happens in a background I/O thread.

`flush(timeout)` **blocks** until all buffered messages have been transmitted to the broker and acknowledged. Without `flush()`:
- The function could return before the last few messages are sent
- The `finally: producer.close()` could terminate the background thread mid-send
- Messages would be silently lost

In this project, `flush(timeout=30)` is called after the publish loop to guarantee every row has been acknowledged before returning the HTTP response.

---

## Q6. What is the Kafka message format used in this project and why?

**Answer:**

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "row_number": 1,
  "timestamp": "2026-07-30T12:00:00.000000",
  "data": {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice.johnson@example.com"
  }
}
```

**Design decisions:**
- **`job_id`** — ties all rows from one upload together for the consumer to group them
- **`row_number`** — 1-based row index; allows the consumer to detect gaps or duplicates
- **`timestamp`** — the exact time the message was produced (not the upload time); useful for latency monitoring and event-time processing
- **`data`** — the actual row payload kept separate from envelope metadata; consumer can extract just this field without parsing the envelope

---

## Q7. What is `NoBrokersAvailable` and when does it occur?

**Answer:**
`NoBrokersAvailable` is a `kafka.errors` exception raised by `kafka-python` when the producer cannot establish a connection to any broker in the `bootstrap_servers` list within the configured timeout.

**Common causes:**
- Kafka container is not running
- Wrong hostname/port in `KAFKA_BOOTSTRAP_SERVERS`
- Network isolation (trying to connect to `kafka:29092` from the host machine instead of inside Docker)
- Kafka still initialising (health check not passed yet)

In this project, `NoBrokersAvailable` is caught in `_build_producer()` and re-raised as a `KafkaPublishError` with HTTP status 503 (Service Unavailable), which the router returns to the client with a descriptive error message.

---

## Q8. Why does `produce_rows_to_kafka` use `future.get(timeout=10)` inside the loop?

**Answer:**
`KafkaProducer.send()` returns a `FutureRecordMetadata` object. Calling `.get(timeout)` blocks until the broker acknowledges the specific message.

**Alternative approach:** Collect all futures in a list, send all messages in the loop, then check futures after — this is faster (fully async send pipeline) but makes it harder to report *which* row failed.

For this project, per-message `.get()` is chosen because:
- The dataset is small (≤ a few thousand rows)
- If row 7 of 15 fails, we report exactly that in the error response
- Correctness is prioritised over throughput at this stage

For Milestone 05+ with large CSVs, a batched approach (collect futures, check after flush) would be more appropriate.

---

## Q9. What is `dataframe.where(pd.notnull(dataframe), None).to_dict(orient='records')`?

**Answer:**
This converts a pandas DataFrame to a list of Python dicts (one dict per row), with `NaN` values (which are floating-point "Not a Number") replaced with Python `None`.

**Why this matters:** pandas represents missing values as `float('nan')`. When `json.dumps()` serialises `float('nan')`, it produces `NaN` — which is **not valid JSON** (the JSON spec only allows `null`, not `NaN`). This would cause a `ValueError` during serialisation.

By replacing `NaN → None` first, `json.dumps()` correctly serialises them as `null` in the Kafka message.

Example:
```python
# Without fix:
{"manager_id": float('nan')}  → json.dumps() → '{"manager_id": NaN}'  ← INVALID JSON
# With fix:
{"manager_id": None}          → json.dumps() → '{"manager_id": null}' ← VALID JSON
```

---

## Q10. What is `value_serializer` in KafkaProducer?

**Answer:**
`value_serializer` is a callable applied to the message value before it is sent. It converts Python objects to bytes (the format Kafka stores and transmits).

In this project:
```python
value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8")
```

- `json.dumps(v, default=str)` — converts dict to JSON string; `default=str` handles any non-JSON-serialisable types (like `datetime` objects) by calling `str()` on them
- `.encode("utf-8")` — converts the JSON string to bytes

Similarly, `key_serializer=lambda k: k.encode("utf-8")` converts the `job_id` string key to bytes. Kafka stores both keys and values as raw bytes — serialisation/deserialisation is the client's responsibility.

---

## Q11. What is the purpose of `max_block_ms` in the producer config?

**Answer:**
`max_block_ms` specifies how long (in milliseconds) `send()` will block if the producer's internal **send buffer** is full.

The internal buffer fills up when:
- Messages are produced faster than the broker can accept them
- The broker is temporarily slow or unavailable

If the buffer fills and `max_block_ms` is exceeded, `send()` raises a `KafkaError` (specifically `BufferError`). Setting `max_block_ms=10_000` (10 seconds) provides a reasonable upper bound before surfacing an error — rather than blocking indefinitely.

---

## Q12. What HTTP status code is returned if Kafka is unavailable, and why?

**Answer:**
**HTTP 503 Service Unavailable.**

RFC 7231 defines 503 as: *"The server is currently unable to handle the request due to a temporary overload or scheduled maintenance, which will likely be alleviated after some delay."*

This is semantically correct: the API server itself is running fine, but a **downstream dependency** (Kafka) is unavailable. The client's request was valid — retrying later may succeed.

Using 500 (Internal Server Error) would be misleading — 500 implies a code bug or unexpected crash, not a dependency outage. Using 503 correctly communicates the nature of the failure and allows HTTP clients/proxies to implement retry logic.

---

## Q13. How does `kafka-python`'s producer handle retries?

**Answer:**
Setting `retries=3` in the producer configuration enables automatic retry on transient errors (like leader election in progress, or a temporary network hiccup). The producer will:

1. Attempt to send the message
2. If it receives a retriable error (e.g., `NotLeaderForPartitionError`, `RequestTimedOutError`), it waits `retry_backoff_ms` (500 ms) and tries again
3. After `retries=3` attempts, if still failing, it raises a `KafkaError`

**Non-retriable errors** (like `MessageSizeTooLargeError`) are not retried — they are surfaced immediately.

This is distinct from **application-level retry** — the `retries` config handles broker-level failures at the protocol layer, below the application code.

---

## Q14. Explain the clean architecture separation in Milestone 03.

**Answer:**

```
routers/ingest.py        ← HTTP only: parse file, call service, map to response/error
    ↓
services/ingest_service.py  ← Orchestration: validate → prepare rows → call producer
    ↓
services/kafka_producer.py  ← Kafka only: build producer, serialise, publish, flush, close
    ↓
core/config.py           ← Config only: reads KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
```

**Why this matters:**
- The router has **zero Kafka code** — it only catches `KafkaPublishError` and maps it to an HTTP response
- `ingest_service.py` orchestrates the flow but doesn't know how Kafka works internally
- `kafka_producer.py` is a self-contained Kafka module — it can be swapped for a different broker (RabbitMQ, AWS SQS) without touching the router or ingest service
- Unit tests can test `ingest_service.py` by mocking `publish_rows_to_kafka` — no real Kafka needed

---

## Q15. What is the `KAFKA_AUTO_CREATE_TOPICS_ENABLE=true` setting in docker-compose.yml?

**Answer:**
This Kafka broker setting allows producers to create topics automatically on first use, without requiring an admin to run `kafka-topics.sh --create` first.

In this project, the `customer-data` topic does not need to be pre-created. When the API first publishes a message, Kafka auto-creates the topic with default settings:
- `KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1` (single broker)
- Default partition count (1)

**In production**, `auto.create.topics.enable=false` is the best practice — topics should be explicitly created with specified partition counts and replication factors. Auto-creation can lead to topics being created with wrong settings due to client misconfiguration.

---

## Q16. What does `producer.close(timeout=10)` do in the `finally` block?

**Answer:**
`close()` performs an orderly shutdown of the producer:
1. Waits up to `timeout` seconds for any remaining buffered messages to be sent
2. Closes the network connections to all brokers
3. Stops the background I/O and metadata threads

Placing `close()` in a `finally` block ensures it **always** runs — whether publishing succeeded or raised an exception. This prevents:
- Thread leaks (background Kafka threads left running)
- Connection leaks (TCP connections to brokers not released)
- `ResourceWarning` from Python's garbage collector

---

## Q17. What Kafka topic is used and how would you inspect messages in it?

**Answer:**
**Topic name:** `customer-data` (configurable via `KAFKA_TOPIC` env var)

To inspect messages from the command line:

```bash
# List all topics
docker exec graphchat-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Describe the customer-data topic
docker exec graphchat-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic customer-data

# Consume all messages from the beginning
docker exec graphchat-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customer-data \
  --from-beginning
```

The last command will print each JSON message to stdout, one per line.

---

## Q18. What would happen if the API publishes 15 messages but Kafka acknowledges only 10?

**Answer:**
Because we call `future.get(timeout=10)` for each message individually inside the loop:

1. Messages 1-10 complete successfully, incrementing `messages_published` to 10
2. Message 11's `future.get()` raises a `KafkaError`
3. The `except KafkaError` block catches it, logs `"Publish failed | row=11"`, and raises `KafkaPublishError`
4. `KafkaPublishError` propagates up to the router
5. The `finally` block runs `producer.close()`
6. The router catches `KafkaPublishError` and returns HTTP 500 with the error message

**Consequence:** The client receives a 500 error. Messages 1-10 are durably stored in Kafka. The client may retry the upload — because we don't have idempotency keys at this stage, this would produce duplicate messages 1-10 in Kafka. Deduplication would need to be handled by the Loader in Milestone 04.

---

## Q19. What is the difference between PLAINTEXT port 29092 and PLAINTEXT_HOST port 9092?

**Answer:**
Kafka is configured with two listeners:

| Listener         | Port  | Advertised address  | Used by                       |
|------------------|-------|---------------------|-------------------------------|
| `PLAINTEXT`      | 29092 | `kafka:29092`       | Services inside Docker network |
| `PLAINTEXT_HOST` | 9092  | `localhost:9092`    | Clients on the host machine   |

The API container sets `KAFKA_BOOTSTRAP_SERVERS=kafka:29092` — it uses the internal listener. Docker's DNS resolves `kafka` to the `graphchat-kafka` container's IP.

If the API tried to connect to `localhost:9092`, it would connect to its own loopback interface — not the Kafka container — and fail with `NoBrokersAvailable`.

---

## Q20. How would you verify that messages were actually received by Kafka after uploading a CSV?

**Answer:**

**Step 1:** Upload a CSV:
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
# Expect: {"job_id":"...","rows":15,"messages_published":15,"topic":"customer-data","status":"published"}
```

**Step 2:** Consume messages from Kafka:
```bash
docker exec graphchat-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic customer-data \
  --from-beginning \
  --max-messages 15
```

**Expected output:** 15 JSON lines, each containing `job_id`, `row_number`, `timestamp`, and `data`.

**Step 3:** Check topic metadata:
```bash
docker exec graphchat-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic customer-data
```

**Step 4:** Check API logs:
```bash
docker compose logs api | findstr "Published\|Publish\|Pipeline complete"
```
