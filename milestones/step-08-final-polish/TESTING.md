# TESTING.md – GraphChatEngine

> Complete test execution guide for Milestone 01.5 (Project Hardening).
> No special tools required — all tests use Docker, curl, and a browser.

---

## Prerequisites

- All containers running: `docker compose up -d`
- curl.exe available (bundled with Windows 10+, Git Bash, or WSL)
- Browser for Swagger UI and Neo4j Browser

---

## 1. Verify Docker — All Containers Running

```bash
docker compose ps
```

**Expected output:**

```
NAME               STATUS                  PORTS
graphchat-api      Up X minutes (healthy)  0.0.0.0:8000->8000/tcp
graphchat-kafka    Up X minutes (healthy)  0.0.0.0:9092->9092/tcp
graphchat-neo4j    Up X minutes (healthy)  0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
graphchat-loader   Up X minutes
```

> ✅ All four containers must be `Up`. API, Kafka, and Neo4j must show `(healthy)`.

### Check individual container health details

```bash
docker inspect graphchat-api --format "{{json .State.Health.Status}}"
# Expected: "healthy"

docker inspect graphchat-kafka --format "{{json .State.Health.Status}}"
# Expected: "healthy"

docker inspect graphchat-neo4j --format "{{json .State.Health.Status}}"
# Expected: "healthy"
```

### View health check logs (debugging unhealthy containers)

```bash
docker inspect graphchat-api --format "{{json .State.Health}}"
```

---

## 2. Verify API — Root and Health Endpoints

### Root endpoint

```bash
curl.exe http://localhost:8000/
```

**Expected response (HTTP 200):**

```json
{
  "status": "running",
  "service": "api",
  "milestone": "02-csv-upload"
}
```

### Health endpoint

```bash
curl.exe http://localhost:8000/health
```

**Expected response (HTTP 200):**

```json
{
  "status": "ok"
}
```

---

## 3. Verify Swagger UI

1. Open a browser and navigate to: **http://localhost:8000/docs**
2. You should see the FastAPI interactive Swagger UI
3. Verify these endpoints are listed:
   - `GET /` — Root
   - `GET /health` — Health Check
   - `POST /ingest` — Upload and validate a CSV file

### Test POST /ingest via Swagger

1. Click **POST /ingest**
2. Click **Try it out**
3. Click **Choose File** and select `sample-data/customers.csv`
4. Click **Execute**

**Expected response:**

```json
{
  "job_id": "<uuid>",
  "filename": "customers.csv",
  "rows": 15,
  "columns": 8,
  "column_names": ["id","name","email","age","city","country","joined_date","tier"],
  "size_kb": 0.93,
  "status": "validated",
  "timestamp": "2026-07-30T..."
}
```

---

## 4. Verify Neo4j Browser

1. Open: **http://localhost:7474**
2. Login with:
   - Username: `neo4j`
   - Password: value from your `.env` file (default: `changeme`)
3. Run a test Cypher query in the query bar:

```cypher
RETURN "GraphChatEngine connected!" AS message
```

**Expected result:** A table showing `message: GraphChatEngine connected!`

> At this milestone, the graph is empty — no nodes have been loaded yet. That is expected.

---

## 5. Verify Kafka

### Check Kafka broker is responsive

```bash
docker exec graphchat-kafka /opt/kafka/bin/kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092
```

**Expected:** A list of API versions supported by the broker (no error).

### List existing topics

```bash
docker exec graphchat-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list
```

**Expected at this milestone:** Empty (no topics created yet) or only internal `__consumer_offsets`.

---

## 6. CSV Upload — Full Test Suite

Run all test cases:

```bash
# ✅ PASS — Valid customers CSV (HTTP 200)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"

# ✅ PASS — Valid employees CSV (HTTP 200)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/employees.csv"

# ✅ PASS — Valid products CSV (HTTP 200)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/products.csv"

# ✅ PASS — Valid orders CSV (HTTP 200)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/orders.csv"

# ❌ REJECTED — Wrong extension (HTTP 400)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.txt"

# ❌ REJECTED — Headers only, no data rows (HTTP 400)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/empty.csv"

# ❌ REJECTED — Malformed CSV content (HTTP 422)
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.csv"
```

### Expected responses summary

| Test File         | Expected HTTP | Expected JSON key    |
|-------------------|---------------|----------------------|
| `customers.csv`   | 200           | `"status":"validated"` |
| `employees.csv`   | 200           | `"status":"validated"` |
| `products.csv`    | 200           | `"status":"validated"` |
| `orders.csv`      | 200           | `"status":"validated"` |
| `invalid.txt`     | 400           | `"error":"Only CSV..."` |
| `empty.csv`       | 400           | `"error":"...no data rows..."` |
| `invalid.csv`     | 422           | `"error":"Unable to parse..."` |

---

## 7. View Container Logs

```bash
# All services
docker compose logs

# API only (follow)
docker compose logs -f api

# Loader only
docker compose logs -f loader

# Kafka only
docker compose logs -f kafka

# Last 50 lines from API
docker compose logs --tail=50 api
```

### What to look for in API logs

After a successful CSV upload, you should see lines like:

```
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Upload started | filename=customers.csv
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Validation success | filename=customers.csv | rows=15 | columns=8 | size_kb=0.93
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Job created | job_id=<uuid> | filename=customers.csv
```

---

## 8. Common Troubleshooting

| Symptom                              | Diagnosis                                    | Fix                                                  |
|--------------------------------------|----------------------------------------------|------------------------------------------------------|
| API shows `unhealthy`                | Health check command not found               | Fixed: now uses Python urllib (no wget/curl needed)  |
| `connection refused` on port 8000    | API container not started                    | Check `docker compose ps` — is graphchat-api running?|
| `500 Internal Server Error`          | Python import error or unhandled exception   | Check `docker compose logs api`                      |
| Neo4j Browser login fails            | Password mismatch                            | Check `NEO4J_PASSWORD` in `.env` matches `NEO4J_AUTH`|
| Kafka check returns `LEADER_NOT_AVAILABLE` | Kafka still initializing              | Wait 30 seconds and retry                            |
| `docker compose up` fails            | Port already in use on host                  | Run `netstat -ano | findstr :8000` and kill the process|
| API logs show `ModuleNotFoundError`  | PYTHONPATH not set correctly                 | Rebuild: `docker compose up --build`                 |

---

## 9. Quick Smoke Test (Copy-Paste)

Run this block to verify everything in one shot:

```bash
echo "=== API Root ===" && curl.exe -s http://localhost:8000/ 
echo "" && echo "=== Health Check ===" && curl.exe -s http://localhost:8000/health
echo "" && echo "=== CSV Upload (customers) ===" && curl.exe -s -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
echo "" && echo "=== Reject TXT file ===" && curl.exe -s -X POST http://localhost:8000/ingest -F "file=@sample-data/invalid.txt"
echo "" && echo "=== Container Status ===" && docker compose ps
```
