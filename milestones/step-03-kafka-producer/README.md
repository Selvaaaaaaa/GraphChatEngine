# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built incrementally during a software hackathon.

[![Status](https://img.shields.io/badge/milestone-01.5%20hardening-blue)]()
[![Python](https://img.shields.io/badge/python-3.11-green)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)]()
[![Kafka](https://img.shields.io/badge/Kafka-3.7%20KRaft-orange)]()
[![Neo4j](https://img.shields.io/badge/Neo4j-5.19%20Community-purple)]()

---

## Overview

GraphChatEngine is a production-style, containerised pipeline that:

1. **Ingests** CSV files through a validated REST API
2. **Streams** rows through Apache Kafka (Milestone 03)
3. **Stores** entities and relationships in a Neo4j graph database (Milestone 04)
4. **Answers** natural-language questions via a chatbot UI (Milestone 05)

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
                        │       │              │                       │
                        │       │         ┌────▼────┐                 │
                        │       │         │ Loader  │                 │
                        │       │         │(worker) │                 │
                        │       │         └────┬────┘                 │
                        │       │              │                       │
                        │       └──────────────▼──────────────────┐   │
                        │                  ┌──────┐                │   │
                        │                  │Neo4j │◄───────────────┘   │
                        │                  │:7474 │                    │
                        │                  │:7687 │                    │
                        │                  └──────┘                    │
                        └─────────────────────────────────────────────┘
```

**Data flow:**
1. Client uploads CSV → `POST /ingest` on the API
2. API validates & produces rows → Kafka topic `csv-records`
3. Loader consumes from Kafka → writes nodes/edges to Neo4j
4. Client queries graph → chatbot returns natural-language answers

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
│   │   └── ingest_service.py   # CSV validation & metadata logic
│   ├── utils/
│   │   └── file_helpers.py     # Stateless helpers
│   ├── main.py                 # App factory — registers routers only
│   ├── requirements.txt
│   └── Dockerfile
├── loader/                     # Internal worker service (Python)
│   ├── loader.py               # Kafka consumer → Neo4j writer (Milestone 03+)
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
│   ├── VIVA_MILESTONE_01.md    # 20 viva Q&As
│   └── REPORT_MILESTONE_01.md  # Copy-ready report content
├── milestones/                 # Immutable snapshots per milestone
│   ├── step-01-project-foundation/
│   ├── step-01.5-project-hardening/
│   └── step-02-csv-upload/
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
| Python            | 3.11          | API and Loader runtime                    |
| FastAPI           | 0.111.0       | REST API framework with OpenAPI/Swagger   |
| Uvicorn           | 0.29.0        | ASGI web server                           |
| pandas            | 2.2.2         | CSV parsing and validation                |
| Apache Kafka      | 3.7.0 KRaft   | Message broker (no ZooKeeper)             |
| Neo4j Community   | 5.19          | Graph database                            |
| Docker            | 24+           | Container runtime                         |
| Docker Compose    | 2+            | Multi-service orchestration               |
| Pydantic          | 2.x           | Data validation and serialization         |

---

## Docker Services

| Service        | Container Name     | Image                         | Purpose                                 |
|----------------|--------------------|-------------------------------|-----------------------------------------|
| `kafka`        | `graphchat-kafka`  | `apache/kafka:3.7.0`          | Message broker in KRaft mode            |
| `neo4j`        | `graphchat-neo4j`  | `neo4j:5.19-community`        | Graph database                          |
| `api`          | `graphchat-api`    | Built from `api/Dockerfile`   | REST API — CSV upload, health checks    |
| `loader`       | `graphchat-loader` | Built from `loader/Dockerfile`| Worker — Kafka consumer (future)        |

---

## Ports

| Service       | Port(s)          | Protocol | Access                            |
|---------------|------------------|----------|-----------------------------------|
| API           | `8000`           | HTTP     | http://localhost:8000             |
| Neo4j Browser | `7474`           | HTTP     | http://localhost:7474             |
| Neo4j Bolt    | `7687`           | Bolt     | bolt://localhost:7687             |
| Kafka         | `9092`           | TCP      | localhost:9092 (external)         |
| Kafka         | `29092` (internal)| TCP     | kafka:29092 (Docker network only) |

---

## How to Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.x
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x (included with Docker Desktop)
- Git

### Step-by-step

```bash
# 1. Clone
git clone https://github.com/Selvaaaaaaa/GraphChatEngine.git
cd GraphChatEngine

# 2. Configure
cp .env.example .env
# Edit .env — at minimum change NEO4J_PASSWORD

# 3. Start all services
docker compose up --build

# 4. Run detached (background)
docker compose up --build -d

# 5. Stop
docker compose down

# 6. Stop and wipe all data volumes
docker compose down -v
```

---

## Health Checks

Each service exposes a Docker health check. After startup:

```bash
docker ps
```

Expected output (all services should show `healthy`):

```
NAMES               STATUS
graphchat-api       Up X minutes (healthy)
graphchat-kafka     Up X minutes (healthy)
graphchat-neo4j     Up X minutes (healthy)
graphchat-loader    Up X minutes
```

### How health checks work

| Service  | Check Method                          | Why                                               |
|----------|---------------------------------------|---------------------------------------------------|
| `api`    | `python -c "urllib.request.urlopen(…)"` | wget/curl absent in python:3.11-slim; Python always available |
| `kafka`  | `kafka-broker-api-versions.sh`        | Native Kafka CLI tool confirms broker is accepting connections |
| `neo4j`  | `wget http://localhost:7474`          | Neo4j image includes wget                        |
| `loader` | No health check (internal worker)     | No HTTP interface to probe                        |

---

## How to Test

### Swagger UI (interactive, easiest)

```
http://localhost:8000/docs
```

1. Click **POST /ingest**
2. Click **Try it out**
3. Upload a file from `sample-data/`
4. Click **Execute**

### curl — happy path

```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/employees.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/products.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/orders.csv"
```

### curl — error paths

```bash
# Wrong extension → HTTP 400
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.txt"

# Headers only → HTTP 400
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/empty.csv"

# Malformed CSV → HTTP 422
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.csv"
```

---

## Common Problems

| Problem                           | Likely Cause                            | Solution                                              |
|-----------------------------------|-----------------------------------------|-------------------------------------------------------|
| API container shows `unhealthy`   | wget not in python:3.11-slim            | Already fixed — uses Python urllib health check       |
| `docker compose up` fails         | Port conflict (8000, 7474, 9092)        | Stop other services or change port mapping in compose |
| Neo4j login rejected              | Wrong password in .env                  | Check NEO4J_PASSWORD matches NEO4J_AUTH format        |
| API returns 503 on startup        | Kafka or Neo4j not yet healthy          | Wait — `depends_on: condition: service_healthy` retries|
| `from api.xxx import` fails       | PYTHONPATH not set                      | Dockerfile sets `ENV PYTHONPATH=/app` — rebuild       |
| Container name conflict           | Stale containers from previous run      | Run `docker compose down` then `docker compose up`    |

---

## Milestones

| #     | Name                    | Status      |
|-------|-------------------------|-------------|
| 01    | Project Foundation      | ✅ Complete |
| 01.5  | Project Hardening       | ✅ Complete |
| 02    | CSV Upload & Validate   | ✅ Complete |
| 03    | Kafka Producer          | 🔜 Planned  |
| 04    | Neo4j Integration       | 🔜 Planned  |
| 05    | Chatbot / NLP           | 🔜 Planned  |

---

## License

MIT
