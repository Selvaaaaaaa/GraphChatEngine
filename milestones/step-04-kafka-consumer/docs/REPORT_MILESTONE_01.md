# REPORT NOTES – Milestone 01 & 01.5: Project Foundation & Hardening

> Ready-to-copy sections for the project report. Covers infrastructure setup, architecture, challenges, and testing.

---

## Objective

The objective of Milestones 01 and 01.5 was to establish a **production-quality project skeleton** for the GraphChatEngine — a CSV-to-Neo4j data pipeline with a chatbot interface. The foundation phase prioritised infrastructure correctness, developer experience, and documentation quality over feature implementation.

Specific goals:
- Deploy all four services (API, Kafka, Neo4j, Loader) with a single `docker compose up --build` command
- Ensure all containers report `healthy` in Docker's health monitoring
- Prepare realistic sample datasets for demonstration in future milestones
- Document the architecture, testing procedures, and viva preparation material

---

## Architecture

The system follows a **microservices architecture** with four independently containerised services, all communicating over a dedicated Docker bridge network (`graphchat-net`):

```
CSV File → FastAPI (POST /ingest) → Kafka (csv-records topic) → Loader → Neo4j
```

| Service      | Technology              | Role                                    |
|--------------|-------------------------|-----------------------------------------|
| `api`        | FastAPI 0.111 + Python 3.11 | REST API, CSV validation, job creation |
| `kafka`      | Apache Kafka 3.7.0 KRaft | Asynchronous message broker            |
| `loader`     | Python 3.11             | Kafka consumer and Neo4j writer         |
| `neo4j`      | Neo4j 5.19 Community    | Graph database                          |

The API uses a **clean architecture** pattern with five distinct layers:
- `routers/` — HTTP boundary (request parsing, response mapping)
- `services/` — Business logic (validation, metadata extraction)
- `schemas/` — Data contracts (Pydantic models)
- `utils/` — Stateless helper functions
- `core/` — Cross-cutting concerns (configuration, logging)

---

## Technologies Used

| Technology        | Version    | Justification                                                    |
|-------------------|------------|------------------------------------------------------------------|
| Python            | 3.11       | Latest stable release with improved performance over 3.10        |
| FastAPI           | 0.111.0    | Auto-generates Swagger UI, async support, Pydantic integration   |
| Uvicorn           | 0.29.0     | High-performance ASGI server for production and development       |
| pandas            | 2.2.2      | Industry-standard CSV parsing; handles edge cases automatically   |
| Apache Kafka      | 3.7.0      | Production-grade message streaming; KRaft mode removes ZooKeeper dependency |
| Neo4j Community   | 5.19       | Native graph storage; optimal for multi-hop relationship queries  |
| Docker            | 24+        | Reproducible, isolated container environments                    |
| Docker Compose    | 2+         | Multi-service orchestration with dependency ordering             |
| Pydantic          | 2.x        | Data validation, serialization, and OpenAPI schema generation    |

---

## Challenges

### Challenge 1: API Container Permanently Unhealthy

**Problem:** After deployment, the API container consistently showed `(unhealthy)` status in `docker ps`. The container itself was running correctly — the FastAPI application was serving requests successfully. However, Docker's health monitoring reported failure on every cycle.

**Root Cause:** The docker-compose.yml health check used `wget -qO- http://localhost:8000/health`. The base image `python:3.11-slim` does not include `wget` (or `curl`). Since the binary was missing, the health check silently failed with exit code 1 on every attempt, resulting in permanent `unhealthy` status.

**Diagnosis method:**
```bash
docker inspect graphchat-api --format "{{json .State.Health}}"
# Output showed ExitCode: 1 and Output: "" for all attempts
# Empty output confirmed the command itself was not found
```

**Solution:** Replace `wget` with Python's built-in `urllib` standard library:
```
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

**Why this solution:** Python is guaranteed to be present in `python:3.11-slim`. `urllib.request` is part of the standard library (no extra packages). The `urlopen()` call raises an exception on any non-2xx response or connection failure, correctly signalling a non-zero exit code to Docker.

---

### Challenge 2: Package Import Resolution Inside Docker

**Problem:** The API used absolute imports (`from api.services.ingest_service import ...`) which failed inside the container with `ModuleNotFoundError: No module named 'api'`.

**Root Cause:** The source code was copied to `/app/api/` but Python's `sys.path` only included `/app/api/` by default, not `/app/`.

**Solution:** Set `ENV PYTHONPATH=/app` in the Dockerfile. This adds `/app` to Python's search path, making `api` resolvable as a package at `/app/api/`.

---

### Challenge 3: Docker Container Naming Conflicts

**Problem:** Running `docker compose up --build` while containers were already running produced `Error response from daemon: Conflict. The container name is already in use` errors.

**Root Cause:** Docker Compose attempted to recreate containers with the same `container_name` values, but old containers were still registered (even if stopped).

**Solution:** Always run `docker compose down` before a full rebuild: `docker compose down && docker compose up --build -d`

---

## Solutions Implemented

1. **Health check fix** — Replaced `wget` with `python -c "urllib.request.urlopen(...)"` in both `api/Dockerfile` and `docker-compose.yml`
2. **PYTHONPATH** — Added `ENV PYTHONPATH=/app` to Dockerfile for correct package import resolution
3. **Clean architecture** — Introduced `routers/`, `services/`, `schemas/`, `utils/`, `core/` layers to prevent logic accumulation in `main.py`
4. **Layered environment configuration** — `core/config.py` reads all env vars in one place; no `os.getenv()` calls scattered throughout the codebase
5. **Centralised logging** — `core/logging_config.py` configures the root logger once at startup; all modules use `logging.getLogger(__name__)`
6. **Sample datasets** — Four realistic CSV files (`customers`, `employees`, `products`, `orders`) designed to demonstrate graph relationships in later milestones
7. **Comprehensive documentation** — `TESTING.md`, `docs/architecture.md`, `docs/VIVA_MILESTONE_01.md`, and updated `README.md`

---

## Testing

### Test Environment
- Docker Desktop 24.x on Windows
- All four containers running via `docker compose up --build -d`
- Testing performed via curl.exe and Swagger UI

### Test Results

| Test                            | Expected    | Result |
|---------------------------------|-------------|--------|
| `docker ps` shows all healthy   | All healthy | ✅ Pass |
| `GET /` returns running status  | HTTP 200    | ✅ Pass |
| `GET /health` returns ok        | HTTP 200    | ✅ Pass |
| Swagger UI loads at `/docs`     | UI renders  | ✅ Pass |
| Upload `customers.csv`          | HTTP 200, 15 rows | ✅ Pass |
| Upload `employees.csv`          | HTTP 200, 15 rows | ✅ Pass |
| Upload `invalid.txt`            | HTTP 400    | ✅ Pass |
| Upload `empty.csv`              | HTTP 400    | ✅ Pass |
| Upload `invalid.csv`            | HTTP 422    | ✅ Pass |
| Neo4j Browser accessible        | Login works | ✅ Pass |
| Kafka broker API versions       | List returned | ✅ Pass |

---

## Screenshots to Capture

1. **`docker ps` output** — all four containers with `(healthy)` status
2. **Swagger UI** (`http://localhost:8000/docs`) — showing all three endpoints
3. **POST /ingest — successful response** — HTTP 200 with full metadata JSON including `job_id`, `rows`, `column_names`
4. **POST /ingest — error response** — HTTP 400 for `invalid.txt`
5. **Neo4j Browser** (`http://localhost:7474`) — connected and showing empty graph
6. **Docker logs** (`docker compose logs api`) — showing the INFO-level log lines for a CSV upload
7. **VS Code file explorer** — showing the clean architecture folder structure
8. **Architecture diagram** — from `docs/architecture.md`

---

## Limitations

| Limitation                            | Description                                                  |
|---------------------------------------|--------------------------------------------------------------|
| No Kafka producer                     | CSV rows validated but not streamed — Milestone 03           |
| No Neo4j writes                       | Graph database is empty — Milestone 04                       |
| No job persistence                    | Job IDs exist only in the HTTP response, not stored anywhere |
| Single-node Kafka                     | Replication factor 1 — not fault-tolerant                    |
| No authentication on API              | All endpoints are public — suitable for development only     |
| Neo4j Community Edition               | No clustering, no advanced security features                 |
| Loader is a no-op                     | Sleeps in a loop — Milestone 03 adds actual consumer logic   |

---

## Future Work

| Milestone | Feature                                      |
|-----------|----------------------------------------------|
| 03        | Kafka producer in API — stream CSV rows to `csv-records` topic |
| 03        | Kafka consumer in Loader — read and log messages               |
| 03        | UI upload form with drag-and-drop support                      |
| 04        | Neo4j Cypher MERGE to create nodes from CSV rows               |
| 04        | Graph schema design (Customer, Product, Order, City nodes)     |
| 04        | Job status tracking endpoint (`GET /jobs/{job_id}`)            |
| 05        | Natural-language query interface                               |
| 05        | Cypher query generation from user questions                    |
| 05        | Chat UI with conversation history                              |
| Future    | API authentication (JWT or API keys)                           |
| Future    | CSV schema validation (column name allowlist)                  |
| Future    | Streaming upload for large CSV files (> 100 MB)                |
