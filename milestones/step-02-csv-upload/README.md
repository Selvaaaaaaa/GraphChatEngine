# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built for hackathon development.

---

## Overview

GraphChatEngine is a production-style, containerised pipeline that:

1. **Ingests** CSV files through a REST API
2. **Streams** records through Apache Kafka
3. **Stores** entities and relationships in a Neo4j graph database
4. **Answers** natural-language questions about the data via a chatbot UI

The project is developed **incrementally across milestones**, starting with a clean infrastructure skeleton and progressively adding business logic.

---

## Folder Structure

```
GraphChatEngine/
├── api/
│   ├── core/
│   │   ├── config.py          # Centralised settings from env vars
│   │   └── logging_config.py  # Logging setup (called once at startup)
│   ├── routers/
│   │   └── ingest.py          # POST /ingest — thin HTTP layer
│   ├── schemas/
│   │   └── ingest.py          # Pydantic request/response models
│   ├── services/
│   │   └── ingest_service.py  # CSV validation & metadata extraction
│   ├── utils/
│   │   └── file_helpers.py    # Stateless helper functions
│   ├── main.py                # App factory — registers routers only
│   ├── requirements.txt
│   └── Dockerfile
├── loader/
│   ├── loader.py
│   ├── requirements.txt
│   └── Dockerfile
├── ui/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample-data/
│   ├── test.csv               # 15-row valid CSV for happy-path testing
│   └── invalid.csv            # Malformed file for error-path testing
├── milestones/
│   ├── step-01-project-foundation/
│   └── step-02-csv-upload/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Services

| Service  | Image / Build                    | Port(s)        | Purpose                                      |
|----------|----------------------------------|----------------|----------------------------------------------|
| `kafka`  | `apache/kafka:3.7.0`             | `9092`         | Message broker (KRaft, no ZooKeeper)         |
| `neo4j`  | `neo4j:5.19-community`           | `7474`, `7687` | Graph database (Browser + Bolt)              |
| `api`    | Built from `./api/Dockerfile`    | `8000`         | FastAPI backend — CSV upload, chat endpoints |
| `loader` | Built from `./loader/Dockerfile` | —              | Internal worker — reads Kafka, writes Neo4j  |

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.x
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x (bundled with Docker Desktop)

### 1 — Clone the repository

```bash
git clone https://github.com/Selvaaaaaaa/GraphChatEngine.git
cd GraphChatEngine
```

### 2 — Configure environment variables

```bash
cp .env.example .env
# Edit .env and set a strong NEO4J_PASSWORD
```

### 3 — Start all services

```bash
docker compose up --build
```

The first run downloads images and builds containers (~3–5 min).

### 4 — Verify services

| Service         | URL                             |
|-----------------|---------------------------------|
| API root        | http://localhost:8000/          |
| API health      | http://localhost:8000/health    |
| **Swagger UI**  | **http://localhost:8000/docs**  |
| Neo4j Browser   | http://localhost:7474           |
| UI              | Open `ui/index.html` in browser |

### Stopping

```bash
docker compose down          # Stop and remove containers
docker compose down -v       # Also remove named volumes (data loss!)
```

---

## Milestone 02 — Testing the CSV Upload Endpoint

### Using Swagger UI (easiest)

1. Open http://localhost:8000/docs
2. Expand **POST /ingest**
3. Click **Try it out**
4. Upload `sample-data/test.csv`
5. Click **Execute**

### Using curl

```bash
# Happy path — valid CSV
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample-data/test.csv"

# Error path — wrong extension
curl -X POST http://localhost:8000/ingest \
  -F "file=@README.md"

# Error path — malformed CSV
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample-data/invalid.csv"
```

### Expected Responses

#### ✅ Success (HTTP 200)

```json
{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "test.csv",
  "rows": 15,
  "columns": 6,
  "column_names": ["id", "name", "email", "age", "city", "country"],
  "size_kb": 0.72,
  "status": "validated",
  "timestamp": "2026-07-30T12:00:00.000000"
}
```

#### ❌ Wrong file type (HTTP 400)

```json
{
  "error": "Only CSV files are supported. Received: 'README.md'. Please upload a file with the .csv extension."
}
```

#### ❌ Empty file (HTTP 400)

```json
{
  "error": "CSV file is empty. Please upload a file with content."
}
```

#### ❌ Malformed CSV (HTTP 422)

```json
{
  "error": "Unable to parse CSV. The file may be malformed or corrupted."
}
```

---

## API Documentation

### `POST /ingest`

| Property         | Value                 |
|------------------|-----------------------|
| **Method**       | POST                  |
| **Content-Type** | `multipart/form-data` |
| **Parameter**    | `file` (UploadFile)   |
| **Accepts**      | `.csv` files only     |

**Validation checks performed (in order):**
1. File extension must be `.csv`
2. File must not be empty (0 bytes)
3. File must be parseable by pandas
4. Must contain at least one column header
5. Must contain at least one data row

---

## Milestones

| #  | Name                   | Status      |
|----|------------------------|-------------|
| 01 | Project Foundation     | ✅ Complete |
| 02 | CSV Upload & Validate  | ✅ Complete |
| 03 | Kafka Producer         | 🔜 Planned  |
| 04 | Neo4j Integration      | 🔜 Planned  |
| 05 | Chatbot / NLP          | 🔜 Planned  |

---

## Development Notes

- All services share the `graphchat-net` Docker bridge network.
- Named Docker volumes persist data across container restarts.
- Health checks enforce correct startup order — Kafka & Neo4j must be healthy before API/Loader start.
- The API uses clean architecture: `routers/` → `services/` → `utils/` with `schemas/` and `core/` as support layers.

---

## License

MIT
