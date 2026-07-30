# Next Step – Milestone 03: Kafka Producer & CSV Streaming

## What Milestone 03 Will Implement

Milestone 03 connects the validated CSV to the message bus — the **CSV → Kafka** segment of the pipeline.

### Specific Features

#### 1. API — Kafka Producer in `ingest_service.py`

After successful validation, each row of the DataFrame will be serialised as a JSON message and produced to the `csv-records` Kafka topic. The existing `process_csv_upload()` function will be extended (not replaced) to call a new `KafkaProducerClient`.

#### 2. Kafka Producer Wrapper (`api/kafka/producer.py`)

A reusable, lifecycle-managed Kafka producer:
- Connects to `KAFKA_BOOTSTRAP_SERVERS` on startup
- Produces messages with `job_id` in the message key for ordered consumption
- Closes cleanly on application shutdown

#### 3. Loader — Kafka Consumer (`loader/kafka_consumer.py`)

The `loader.py` infinite-sleep loop is replaced with:
- A `KafkaConsumer` subscribing to `csv-records`
- Per-message logging: job ID, row index, payload preview
- Foundation for Neo4j writes in Milestone 04

#### 4. API Response Extension

The success response will include additional Kafka-related fields:
```json
{
  "job_id": "...",
  "status": "queued",
  "kafka_topic": "csv-records",
  "messages_produced": 15
}
```

#### 5. UI — Upload Form

Replace the "System Initializing" placeholder with:
- A file picker input (`<input type="file" accept=".csv">`)
- An upload button with a spinner
- A results panel displaying the JSON response

#### 6. Kafka Topic Initialization

Add an `init-kafka` service (or entrypoint script) to ensure the `csv-records` topic exists before the API produces to it.

---

## Why It Is the Logical Next Step

Milestone 02 validates CSV data and generates job IDs — the data is ready but going nowhere. Milestone 03 sends it to Kafka, enabling:

- **Decoupling**: The API finishes its work immediately; the Loader processes at its own rate
- **Backpressure**: Kafka absorbs upload spikes without overwhelming Neo4j
- **Observability**: Kafka topics provide a durable log of all uploaded data
- **The Loader has work to do**: Currently it does nothing; Milestone 03 gives it a real job

This is the natural second business-logic milestone because the first thing produced must be consumed before anything useful can be stored.

---

## Files to Modify

| File                          | Change                                                        |
|-------------------------------|---------------------------------------------------------------|
| `api/services/ingest_service.py` | Call Kafka producer after successful validation            |
| `api/requirements.txt`        | Uncomment `kafka-python==2.0.2`                               |
| `loader/loader.py`            | Replace sleep loop with Kafka consumer                        |
| `loader/requirements.txt`     | Uncomment `kafka-python==2.0.2`                               |
| `api/schemas/ingest.py`       | Add `kafka_topic` and `messages_produced` to success response |
| `ui/index.html`               | Add upload form section                                       |
| `ui/style.css`                | Style form and results panel                                  |
| `ui/app.js`                   | Add `uploadCsv()` function                                    |
| `docker-compose.yml`          | Optionally add topic-init container                           |

---

## New Files to Create

| File                                   | Purpose                                        |
|----------------------------------------|------------------------------------------------|
| `api/kafka/__init__.py`                | Package marker                                 |
| `api/kafka/producer.py`                | Reusable Kafka producer wrapper                |
| `loader/kafka_consumer.py`             | Kafka consumer loop                            |
| `milestones/step-03-kafka-producer/`   | Full snapshot of Milestone 03                  |
| `milestones/step-03-kafka-producer/MILESTONE.md` | Milestone 03 documentation           |
| `milestones/step-03-kafka-producer/NEXT_STEP.md` | Points to Milestone 04 (Neo4j)       |
| `milestones/step-03-kafka-producer/VIVA_NOTES.md` | Viva Q&A for Milestone 03           |
| `milestones/step-03-kafka-producer/REPORT_NOTES.md` | Report bullet points              |
