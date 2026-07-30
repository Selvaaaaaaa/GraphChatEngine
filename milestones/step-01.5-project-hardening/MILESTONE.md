# Milestone 01.5 – Project Hardening

## Objective

Improve the existing GraphChatEngine project without adding business logic. This milestone focused on:
1. Fixing the Docker health check that caused the API container to always show `unhealthy`
2. Creating realistic sample datasets for future milestone demonstrations
3. Completing the `.env.example` with full variable documentation
4. Overhauling the README with architecture, port table, and troubleshooting guide
5. Creating a comprehensive TESTING.md guide
6. Producing docs/architecture.md with full ASCII diagram and component explanations
7. Producing docs/VIVA_MILESTONE_01.md with 20 professional viva Q&As
8. Producing docs/REPORT_MILESTONE_01.md with copy-ready report content

---

## Features Completed

- ✅ **Health check fixed** — API container now shows `(healthy)` in `docker ps`
- ✅ **Root cause documented** — `python:3.11-slim` lacks `wget`; Python urllib used instead
- ✅ **Dockerfile updated** — `HEALTHCHECK` directive added with Python urllib
- ✅ **docker-compose.yml updated** — API healthcheck replaced with Python urllib command
- ✅ **customers.csv** — 15 realistic rows (id, name, email, age, city, country, joined_date, tier)
- ✅ **employees.csv** — 15 rows with manager_id hierarchy (org chart relationships)
- ✅ **products.csv** — 15 rows with category/subcategory/supplier links
- ✅ **orders.csv** — 15 rows linking customers to products (PURCHASED relationships)
- ✅ **empty.csv** — Headers only (tests HTTP 400 path)
- ✅ **invalid.txt** — Wrong extension (tests HTTP 400 path)
- ✅ **.env.example** — Every variable documented with purpose, allowed values, and which service uses it
- ✅ **README.md** — Full rewrite with architecture diagram, tech stack table, port table, troubleshooting
- ✅ **TESTING.md** — Complete test guide with expected outputs for all endpoints
- ✅ **docs/architecture.md** — Full ASCII diagram, component descriptions, data flow
- ✅ **docs/VIVA_MILESTONE_01.md** — 20 viva Q&As covering all required topics
- ✅ **docs/REPORT_MILESTONE_01.md** — Copy-ready report with challenges, solutions, test results

---

## What Works

| Feature                               | Status | Notes                                          |
|---------------------------------------|--------|------------------------------------------------|
| `docker ps` shows api as `(healthy)`  | ✅     | Python urllib health check — no wget needed    |
| All four containers start             | ✅     | Via `docker compose up --build`                |
| `GET /` returns milestone 02 status   | ✅     | HTTP 200                                       |
| `GET /health` returns ok              | ✅     | HTTP 200                                       |
| `POST /ingest` with all 4 valid CSVs  | ✅     | customers, employees, products, orders         |
| Swagger UI documents POST /ingest     | ✅     | http://localhost:8000/docs                     |
| Neo4j Browser accessible              | ✅     | http://localhost:7474                          |
| Kafka broker responding               | ✅     | Port 9092 healthy                              |

---

## What Does NOT Work Yet

| Feature                    | Planned Milestone |
|----------------------------|-------------------|
| Kafka producer             | Milestone 03      |
| Kafka consumer (Loader)    | Milestone 03      |
| Neo4j graph writes         | Milestone 04      |
| Cypher queries             | Milestone 04      |
| Chatbot interface          | Milestone 05      |
| UI upload form             | Milestone 03      |
| Job status tracking        | Milestone 04      |

---

## Architecture

```
Browser / curl ──► graphchat-api (FastAPI :8000)
                        │
                        ▼ [Milestone 03]
               graphchat-kafka (KRaft :9092)
                        │
                        ▼ [Milestone 03]
               graphchat-loader (Python worker)
                        │
                        ▼ [Milestone 04]
               graphchat-neo4j (:7474 / :7687)
```

All services share `graphchat-net` Docker bridge network.

---

## Commands

```bash
# Start all services
docker compose up --build -d

# Check container health
docker ps

# Test API
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/

# Test all CSV uploads
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/employees.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/products.csv"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/orders.csv"

# Test error paths
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.txt"
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/empty.csv"

# View API logs
docker compose logs -f api

# Open Swagger UI (Windows)
start http://localhost:8000/docs
start http://localhost:7474
```

---

## Key Decision: Health Check Method

**Problem:** `wget -qO- http://localhost:8000/health` → ExitCode 1, Output: ""

**Why it failed:** `python:3.11-slim` does NOT include `wget` or `curl`. The binary was not found, causing an immediate silent failure.

**Solution chosen:** `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"`

**Why this solution:**
- Python is guaranteed to be in the image
- `urllib.request` is a standard library module — zero extra dependencies
- `urlopen()` raises `URLError` on any failure — Docker interprets the non-zero exit as unhealthy
- Works correctly on HTTP 200 (silent success) and all error conditions (exception = non-zero exit)
- Zero image size overhead
- Most portable approach for Python-based containers

---

## Viva Notes — Key Questions for This Milestone

**Q: Why was the API container unhealthy?**
`python:3.11-slim` doesn't include `wget`. The health check command `wget -qO-...` returned exit code 1 because the binary was missing — not because the API was actually failing.

**Q: What is the best health check method for a python:3.11-slim container?**
Use `python -c "import urllib.request; urllib.request.urlopen(...)"`. Python and urllib are always present; no extra tools needed.

**Q: What is `start_period` in a Docker health check?**
A grace period during which failing health checks do not count toward the retry limit. The API needs time to start Uvicorn before the first check runs. Setting `start_period: 20s` prevents false unhealthy reports during startup.

**Q: Why are there two Kafka port numbers (9092 and 29092)?**
9092 is exposed to the host machine. 29092 is the internal Docker network port. Services inside Docker use `kafka:29092`; the host uses `localhost:9092`. Two listeners are required because the advertised address differs.

**Q: What graph relationships will the sample data enable?**
- customers → orders → products (purchase graph)
- employees → REPORTS_TO → manager (org hierarchy)
- products → suppliers (supply chain)
- customers → city → country (geolocation)

---

## Report Notes

- Milestone 01.5 introduced infrastructure hardening without modifying the application's functional behaviour, following the principle of separating infrastructure concerns from business logic.
- The health check root cause investigation demonstrated the importance of understanding base image contents — `python:3.11-slim` deliberately excludes system tools like `wget` and `curl` to minimise attack surface.
- The fix (Python urllib health check) is the recommended production approach for Python containers and requires zero additional package installations.
- Four sample datasets were designed with inter-dataset foreign keys (`customer_id`, `product_id` in `orders.csv`) to prepare for graph relationship modelling in Milestone 04.
- The documentation suite (`TESTING.md`, `docs/architecture.md`, `docs/VIVA_MILESTONE_01.md`, `docs/REPORT_MILESTONE_01.md`) brings the project to a professional standard suitable for academic and industry evaluation.
