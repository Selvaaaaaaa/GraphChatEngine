# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built incrementally during a software hackathon.

[![Status](https://img.shields.io/badge/milestone-04%20kafka%20consumer-green)]()
[![Python](https://img.shields.io/badge/python-3.11-green)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)]()
[![Kafka](https://img.shields.io/badge/Kafka-3.7%20KRaft-orange)]()
[![Neo4j](https://img.shields.io/badge/Neo4j-5.19%20Community-purple)]()

---

## Overview

GraphChatEngine is a production-style, containerised pipeline that:

1. **Ingests** CSV files through a validated REST API
2. **Streams** rows through Apache Kafka (Milestone 03)
3. **Consumes** & validates messages in real-time worker (Milestone 04)
4. **Stores** entities and relationships in a Neo4j graph database (Milestone 05)
5. **Answers** natural-language questions via a chatbot UI (Milestone 06)

---

## Project Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │           Docker Network: graphchat-net       │
                        │                                               │
  Browser / curl ──────►│  ┌─────────┐    ┌─────────┐                 │
                        │  │   API   │───►│  Kafka  │                 │
                        │  │ :8000   │    │  :9092  │                 │
                        │  │ FastAPI │    │  KRaft  │                 │
                        │  └─────────┘    └────┬────┘                 │
                        │                      │                      │
                        │                 ┌────▼────┐                 │
                        │                 │ Loader  │                 │
                        │                 │ Consumer│                 │
                        │                 └────┬────┘                 │
                        │                      │                      │
                        │                 ┌────▼────┐                 │
                        │                 │  Neo4j  │                 │
                        │                 │  :7474  │                 │
                        │                 │  :7687  │                 │
                        │                 └─────────┘                 │
                        └─────────────────────────────────────────────┘
```

**Data flow:**
1. Client uploads CSV → `POST /ingest` on the API
2. API validates & produces rows → Kafka topic `customer-data`
3. Loader (`loader/consumer.py`) consumes from Kafka → deserializes, validates, logs & stores in memory
4. Neo4j loader stores entities/edges (next milestone)

---

## Folder Structure

```
GraphChatEngine/
├── api/                        # FastAPI application (Python)
│   ├── core/
│   │   ├── config.py           # Centralised settings from env vars
│   │   └── logging_config.py   # Root logger setup
│   ├── routers/
│   │   └── ingest.py           # POST /ingest HTTP handler
│   ├── schemas/
│   │   └── ingest.py           # Pydantic request/response models
│   ├── services/
│   │   ├── ingest_service.py   # CSV validation & orchestration logic
│   │   └── kafka_producer.py   # Kafka producer service
│   ├── utils/
│   │   └── file_helpers.py     # Stateless helpers
│   ├── main.py                 # App factory — registers routers only
│   ├── requirements.txt
│   └── Dockerfile
├── loader/                     # Internal worker service (Python)
│   ├── services/
│   │   ├── __init__.py
│   │   └── kafka_consumer.py   # Kafka consumer service layer
│   ├── consumer.py             # Main consumer execution entrypoint
│   ├── loader.py               # Loader service delegate
│   ├── requirements.txt
│   └── Dockerfile
├── ui/                         # Static browser UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample-data/                # Test CSV files
│   ├── customers.csv           # 15-row customer dataset
│   ├── employees.csv           # 15-row employee hierarchy
│   ├── products.csv            # 15-row product catalogue
│   ├── orders.csv              # 15-row order records
│   ├── empty.csv               # Headers only — tests HTTP 400
│   ├── test.csv                # Generic 15-row valid CSV
│   ├── invalid.csv             # Malformed CSV — tests HTTP 422
│   └── invalid.txt             # Wrong extension — tests HTTP 400
├── docs/
│   ├── architecture.md         # Detailed architecture diagram
│   ├── VIVA_MILESTONE_01.md    # Viva Q&As
│   ├── REPORT_MILESTONE_01.md  # Report content
│   ├── VIVA_MILESTONE_03.md    # Kafka producer viva Q&As
│   ├── REPORT_MILESTONE_03.md  # Kafka producer report
│   ├── VIVA_MILESTONE_04.md    # Kafka consumer viva Q&As
│   └── REPORT_MILESTONE_04.md  # Kafka consumer report
├── milestones/                 # Immutable snapshots per milestone
│   ├── step-01-project-foundation/
│   ├── step-01.5-project-hardening/
│   ├── step-02-csv-upload/
│   ├── step-03-kafka-producer/
│   └── step-04-kafka-consumer/
├── docker-compose.yml
├── .env.example                # Copy to .env — never commit .env
├── .gitignore
├── TESTING.md                  # Test execution guide
└── README.md
```

---

## Technology Stack

| Technology        | Version       | Role                                      |
|-------------------|---------------|-------------------------------------------|
| Python            | 3.11          | API and Loader worker runtime             |
| FastAPI           | 0.111.0       | REST API framework with OpenAPI/Swagger   |
| Uvicorn           | 0.29.0        | ASGI web server                           |
| pandas            | 2.2.2         | CSV parsing and validation                |
| Apache Kafka      | 3.7.0 KRaft   | Message broker (no ZooKeeper)             |
| kafka-python      | 2.0.2         | Kafka producer & consumer library         |
| Neo4j Community   | 5.19          | Graph database                            |
| Docker            | 24+           | Container runtime                         |
| Docker Compose    | 2+            | Multi-service orchestration               |

---

## Kafka Consumer (Milestone 04)

### Consumer Workflow
```
Kafka Topic ("customer-data")
        │
        ▼
   Poll Record
        │
        ▼
Deserialize JSON Payload
        │
        ▼
Validate Message Schema (job_id, row_number, timestamp, data)
        │
        ├── [If Invalid] ──► Log Error & Skip Record (No Crash)
        │
        └── [If Valid] ───► Log Message Success & Store in Memory
```

### Consumer Configuration

Configuration is passed via environment variables (configured in `.env` and `docker-compose.yml`):

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka broker host & port |
| `KAFKA_TOPIC` | `customer-data` | Target topic to consume from |
| `GROUP_ID` | `graphchat-loader-group` | Consumer group identifier |
| `AUTO_OFFSET_RESET` | `earliest` | Offset strategy when no initial offset exists |

---

## How to Start Consumer

The Kafka Consumer starts automatically as part of the `graphchat-loader` container when running Docker Compose:

```bash
# Start all containers in detached mode
docker compose up --build -d

# View live consumer logs
docker compose logs -f loader
```

To run consumer locally outside Docker:
```bash
cd loader
pip install -r requirements.txt
export KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
export KAFKA_TOPIC="customer-data"
export GROUP_ID="graphchat-loader-group"
export AUTO_OFFSET_RESET="earliest"
python consumer.py
```

---

## Testing Instructions

1. Upload a CSV file via API:
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```

2. Observe live consumer logs:
```bash
docker compose logs loader
```

Expected output in consumer logs:
```text
2026-07-30T13:15:20 | INFO     | loader.kafka_consumer | Received Message | Job ID: 12588210-9a39-4710-a8ee-dfe86c7872dc | Row Number: 1 | timestamp: 2026-07-30T13:15:20.088318
Received row 1 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
...
Received row 15 | job_id=12588210-9a39-4710-a8ee-dfe86c7872dc
```

---

## Milestones

| #     | Name                    | Status      |
|-------|-------------------------|-------------|
| 01    | Project Foundation      | ✅ Complete |
| 01.5  | Project Hardening       | ✅ Complete |
| 02    | CSV Upload & Validate   | ✅ Complete |
| 03    | Kafka Producer          | ✅ Complete |
| 04    | Kafka Consumer          | ✅ Complete |
| 05    | Neo4j Integration       | 🔜 Planned  |
| 06    | Chatbot / NLP           | 🔜 Planned  |

---

## License

MIT
