# Next Step – Milestone 02: Kafka Producer & CSV Upload

## What Milestone 02 Will Implement

Milestone 02 adds the **data ingestion pipeline** — the path a CSV file takes from the user's browser to a Kafka topic.

### Specific Features

1. **API – CSV Upload Endpoint** (`POST /upload`)
   - Accepts a multipart CSV file upload
   - Parses each row using Python's `csv` module (or `pandas`)
   - Produces each row as a JSON message to a Kafka topic (`csv-records`)

2. **Kafka Topic Creation**
   - Ensure the `csv-records` topic exists at startup (auto-create or explicit creation)

3. **Loader – Kafka Consumer**
   - Subscribes to the `csv-records` topic
   - Reads and logs each incoming message (Neo4j writes deferred to Milestone 03)

4. **UI – Upload Form**
   - File picker input (`<input type="file" accept=".csv">`)
   - Upload button with progress indicator
   - Response display (success / error message)

---

## Why It Is the Logical Next Step

The project currently has all infrastructure running but **no data flowing**. Milestone 02 closes the first gap in the pipeline: **CSV → Kafka**. This is the natural second step because:

- The Kafka broker is already running and healthy.
- The API and Loader containers are running and ready to receive new code.
- The UI already has a placeholder — it just needs a real upload form.
- Producing to Kafka before consuming (Milestone 03) respects the unidirectional data-flow principle.

---

## Files to Modify

| File                        | Change                                                     |
|-----------------------------|------------------------------------------------------------|
| `api/main.py`               | Add `POST /upload` endpoint with CSV parsing + Kafka producer |
| `api/requirements.txt`      | Uncomment / add `kafka-python==2.0.2`, `python-multipart`  |
| `loader/loader.py`          | Replace `while True: sleep(60)` with Kafka consumer loop   |
| `loader/requirements.txt`   | Uncomment `kafka-python==2.0.2`                            |
| `ui/index.html`             | Add upload form section                                    |
| `ui/style.css`              | Style the upload form and progress indicator               |
| `ui/app.js`                 | Add `uploadCsv()` function and form event listener         |
| `docker-compose.yml`        | Add Kafka topic init container (optional but recommended)  |

---

## New Files to Create

| File                                          | Purpose                                      |
|-----------------------------------------------|----------------------------------------------|
| `api/kafka_producer.py`                       | Reusable Kafka producer wrapper              |
| `loader/kafka_consumer.py`                    | Reusable Kafka consumer wrapper              |
| `milestones/step-02-kafka-producer/`          | Snapshot of Milestone 02 upon completion     |
| `milestones/step-02-kafka-producer/MILESTONE.md` | Milestone 02 documentation               |
| `milestones/step-02-kafka-producer/NEXT_STEP.md` | Points to Milestone 03                   |
