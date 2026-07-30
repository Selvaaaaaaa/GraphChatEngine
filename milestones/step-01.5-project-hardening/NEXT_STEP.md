# Next Step – Milestone 03: Kafka Producer & CSV Streaming

## What Milestone 03 Will Implement

Milestone 03 closes the gap between the validated CSV and the message bus, implementing the **CSV → Kafka** segment of the pipeline.

### Features

1. **Kafka Producer in `api/services/ingest_service.py`**
   - After successful CSV validation, each row is serialised as JSON
   - All rows are produced to the `csv-records` Kafka topic
   - Response extended with `kafka_topic` and `messages_produced` fields

2. **Kafka Producer Wrapper (`api/kafka/producer.py`)**
   - Thread-safe reusable producer with connection lifecycle management
   - Message key = `job_id` (ensures ordered consumption per upload)

3. **Loader — Kafka Consumer (`loader/kafka_consumer.py`)**
   - Replaces the `while True: sleep(60)` loop
   - Subscribes to `csv-records`, reads and logs each message
   - Foundation for Neo4j writes in Milestone 04

4. **UI Upload Form**
   - Drag-and-drop file picker
   - Upload progress indicator
   - Response panel showing job metadata

---

## Why It Is the Logical Next Step

The pipeline currently has a gap: CSV rows are validated but go nowhere. Milestone 03 fills this gap and:
- Gives the Loader something real to do
- Demonstrates Kafka's decoupling role
- Enables observation of messages in real-time via Kafka CLI tools
- Prepares the exact message format that Neo4j will consume in Milestone 04

---

## Files to Modify

| File                             | Change                                                      |
|----------------------------------|-------------------------------------------------------------|
| `api/services/ingest_service.py` | Add Kafka producer call after successful validation         |
| `api/requirements.txt`           | Uncomment `kafka-python==2.0.2`                             |
| `api/schemas/ingest.py`          | Add `kafka_topic`, `messages_produced` to success response  |
| `loader/loader.py`               | Replace sleep loop with Kafka consumer                      |
| `loader/requirements.txt`        | Uncomment `kafka-python==2.0.2`                             |
| `ui/index.html`                  | Add upload form section                                     |
| `ui/style.css`                   | Style form, progress bar, results panel                     |
| `ui/app.js`                      | Add `uploadCsv()` function and event listeners              |

---

## New Files to Create

| File                               | Purpose                                           |
|------------------------------------|---------------------------------------------------|
| `api/kafka/__init__.py`            | Package marker                                    |
| `api/kafka/producer.py`            | Thread-safe Kafka producer wrapper                |
| `loader/kafka_consumer.py`         | Kafka consumer loop with structured logging       |
| `milestones/step-03-kafka-producer/` | Full snapshot of Milestone 03                   |
