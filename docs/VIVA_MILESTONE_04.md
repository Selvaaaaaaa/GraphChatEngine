# VIVA NOTES – Milestone 04: Kafka Consumer

> 20 professional viva questions with detailed answers.
> Covers Kafka Consumer architecture, consumer groups, offsets, deserialization, validation, and error resilience.

---

## Q1. What is a Kafka Consumer and what is its role in this pipeline?

**Answer:**
A Kafka Consumer is a client application that subscribes to one or more Kafka topics and reads event streams published by Kafka producers.

In GraphChatEngine, the Kafka Consumer lives inside the `loader` service (`loader/services/kafka_consumer.py`). Its role is to pull JSON-encoded CSV row messages from the `customer-data` topic, deserialize and validate the message schema, log message reception, and buffer valid messages in memory for graph database ingestion in subsequent milestones.

---

## Q2. What is a Consumer Group and why is it used?

**Answer:**
A **Consumer Group** is a set of consumer instances working together to consume messages from a set of Kafka topics.

**Key benefits:**
1. **Parallelism & Load Balancing:** Kafka automatically assigns partitions among consumers in the same group. If a topic has 4 partitions and a consumer group has 4 consumers, each consumer processes 1 partition concurrently.
2. **High Availability & Rebalancing:** If a consumer instance fails, Kafka reassigns its assigned partitions to the remaining healthy consumers in the group.
3. **Offset Management:** Kafka tracks consumer offsets per consumer group, allowing different consumer groups (e.g., Loader Service vs Analytics Service) to consume the same topic independently at their own pace.

---

## Q3. What is an Offset in Kafka?

**Answer:**
An **offset** is a sequential, 64-bit integer assigned to each message as it arrives in a Kafka partition. Offsets increase monotonically starting from zero.

The offset uniquely identifies a message's position within a partition. Consumers use offsets to track which messages have already been read. By committing offsets (e.g., automatically or manually), a consumer group records its progress so it can resume from where it left off if restarted.

---

## Q4. What is `AUTO_OFFSET_RESET` and what are its options?

**Answer:**
`AUTO_OFFSET_RESET` specifies the strategy a consumer should use when it reads from a topic for the first time (when no committed offset exists for the consumer group) or when its committed offset is invalid/out of range.

**Options:**
- **`earliest`** (used in Milestone 04): Automatically resets the offset to the earliest message in the log. The consumer reads all historical messages from the beginning of the topic.
- **`latest`**: Automatically resets the offset to the latest message. The consumer ignores past messages and reads only new messages published after startup.
- **`none`**: Throws an exception to the consumer if no previous offset is found.

---

## Q5. Why is JSON deserialization necessary in the consumer?

**Answer:**
Kafka is payload-agnostic and stores all message keys and values as raw byte arrays (`bytes`).

When the API (producer) sends messages, it serializes Python dictionaries into UTF-8 JSON bytes (`json.dumps().encode('utf-8')`).

When the consumer receives raw bytes from Kafka, it must perform **deserialization** (`payload.decode('utf-8')` followed by `json.loads()`) to convert the binary payload back into a structured Python dictionary (`dict`) so fields like `job_id`, `row_number`, and `data` can be validated and processed.

---

## Q6. What is the fundamental difference between a Kafka Producer and a Kafka Consumer?

**Answer:**

| Property | Kafka Producer | Kafka Consumer |
|----------|----------------|----------------|
| **Primary Action** | Pushes / Writes messages to Kafka topics | Pulls / Reads messages from Kafka topics |
| **Data Direction** | Application → Kafka Broker | Kafka Broker → Application |
| **Key Responsibilities**| Serialization, partition keying, ack waiting, buffer flushing | Deserialization, offset tracking, message validation, handling poll loop |
| **Role in Pipeline** | API Service (`api/services/kafka_producer.py`) | Loader Service (`loader/services/kafka_consumer.py`) |

---

## Q7. What message validation is performed in Milestone 04?

**Answer:**
Before accepting a record into memory, `IngestConsumerService.validate_message()` checks:
1. Is the deserialized payload a dictionary?
2. Does it contain all four mandatory top-level keys?
   - `job_id` (non-null string)
   - `row_number` (non-null integer)
   - `timestamp` (non-null ISO timestamp string)
   - `data` (non-null dictionary containing column values)

If any required key is missing or null, the message is rejected with an error log and skipped.

---

## Q8. How does the consumer prevent crashing when encountering a malformed message?

**Answer:**
The consumer implements defensive programming and exception isolation:
1. **Deserialization safety:** `json.loads()` is wrapped in a `try...except (json.JSONDecodeError, UnicodeDecodeError)` block. Malformed JSON returns `None` instead of raising an uncaught exception.
2. **Schema validation:** `validate_message()` checks dict types and required keys. Invalid messages trigger a warning log and a `return` to skip processing.
3. **Poll loop exception handling:** The outer processing loop wraps message handling in `try...except Exception`. Any unexpected runtime error for a single message is caught and logged, allowing the loop to continue to the next message.

---

## Q9. Why is clean architecture used in the Loader service?

**Answer:**
Clean architecture isolates concerns into distinct components:
- `loader/services/kafka_consumer.py`: Contains pure Kafka connection, polling, validation, and in-memory storage logic.
- `loader/consumer.py`: Acts as the application entry point, managing execution startup, environment variables, and OS signal handlers (`SIGINT`/`SIGTERM`).

**Benefits:**
- **Testability:** Consumer business logic can be unit-tested without executing process signals.
- **Maintainability:** Adding Neo4j writing in Milestone 05 requires extending the service layer without modifying the entry point process lifecycle.

---

## Q10. What is Kafka polling and how does `consumer.poll(timeout_ms)` work?

**Answer:**
Kafka consumers operate on a **pull model**. The consumer actively requests batches of messages from the broker by calling `consumer.poll(timeout_ms)`.

`poll(timeout_ms=1000)`:
- Blocks for up to 1000 milliseconds waiting for new messages from assigned topic partitions.
- Returns a dictionary mapping `TopicPartition` to a list of `ConsumerRecord` objects.
- If no messages arrive within 1000ms, it returns an empty dictionary `{}`.
- Also performs background heartbeat checks with the Kafka broker to maintain consumer group membership.

---

## Q11. What is automatic offset committing (`enable_auto_commit=True`)?

**Answer:**
When `enable_auto_commit=True` (and `auto_commit_interval_ms=1000`), the Kafka consumer periodically commits the highest read message offset back to Kafka in the background every 1000ms.

**Trade-off:**
- **Pros:** Simple, automatic offset management without manual `commit()` calls.
- **Cons:** Risk of message loss or duplicate processing if the consumer crashes mid-batch between poll intervals. (Manual offset committing after successful DB write is used in advanced production pipelines).

---

## Q12. What environment variables configure the Kafka consumer?

**Answer:**
1. `KAFKA_BOOTSTRAP_SERVERS` — Host and port of Kafka broker (`kafka:29092`).
2. `KAFKA_TOPIC` — Topic name to subscribe to (`customer-data`).
3. `GROUP_ID` — Consumer group identifier (`graphchat-loader-group`).
4. `AUTO_OFFSET_RESET` — Offset reset strategy (`earliest`).

---

## Q13. How does the consumer handle graceful shutdown?

**Answer:**
When Docker sends a termination signal (`SIGTERM` or `SIGINT` / Ctrl+C):
1. The signal handler in `consumer.py` intercepts the signal and calls `consumer_service.stop()`.
2. `stop()` sets `self.running = False`, breaking the main `while` poll loop.
3. `stop()` calls `self.consumer.close(timeout=5)`, which sends a `LeaveGroup` request to Kafka so the broker immediately rebalances the consumer group, and commits final offsets cleanly.

---

## Q14. What happens if the Kafka broker is down when the consumer starts?

**Answer:**
`IngestConsumerService.connect_consumer()` catches `NoBrokersAvailable` exceptions in a `while True` loop with exponential backoff (`time.sleep(2)` increasing up to 30 seconds).

The consumer logs warnings (`"Kafka unavailable | Retrying in X seconds..."`) and continuously retries until Kafka becomes healthy, preventing the loader container from crashing and restarting in a fail loop.

---

## Q15. Why does the consumer log "Consumer Waiting"?

**Answer:**
When `consumer.poll()` returns no records (e.g. when no new CSV files have been uploaded), the consumer enters an idle waiting state. Logging `"Consumer Waiting"` periodically signals that the worker thread is healthy, active, and monitoring the topic for incoming messages.

---

## Q16. How does using `job_id` in message payload help the consumer?

**Answer:**
The `job_id` uniquely identifies the CSV upload batch.
By receiving `job_id` on every row message:
- The consumer can group incoming rows in memory by `job_id`.
- The consumer can track progress (e.g., received 15 out of 15 rows for job `XYZ`).
- In Milestone 05, the consumer can label all created Neo4j graph nodes with `job_id` for traceability.

---

## Q17. What is the role of `row_number` in the message payload?

**Answer:**
`row_number` is a 1-based integer indicating the row's position in the original CSV file.
- It enables ordering verification (e.g. verifying `row_number` sequence 1, 2, 3...).
- It provides human-readable context in consumer logs (`Received row 1 | job_id=...`).
- It helps detect skipped or duplicated rows during debugging.

---

## Q18. How does the consumer store messages in memory during Milestone 04?

**Answer:**
`IngestConsumerService` maintains an in-memory list attribute:
```python
self.memory_store: List[Dict[str, Any]] = []
```
Upon passing validation, each valid message dict is appended: `self.memory_store.append(message_val)`.

This keeps messages available in process memory without persisting to a database, satisfying the Milestone 04 requirement ("Store temporarily in memory; DO NOT insert into Neo4j").

---

## Q19. What python library is used for Kafka consumption in this project?

**Answer:**
`kafka-python==2.0.2`, specified in `loader/requirements.txt`.
It provides the pure-Python `KafkaConsumer` class, supporting consumer groups, automatic deserialization, offset management, and topic subscription.

---

## Q20. What is the stop condition for Milestone 04?

**Answer:**
The stop condition is reached when the Kafka consumer continuously receives, deserializes, validates, logs, and stores CSV row messages in memory upon CSV upload. No Neo4j nodes or relationships are created in this milestone.
