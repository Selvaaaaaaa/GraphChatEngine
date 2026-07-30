# GraphChatEngine – Hackathon Live Demonstration Script

> Step-by-Step Live Demo Execution Guide for Judges & Technical Reviewers.

---

## Live Demo Sequence (12 Steps)

### Step 1: Start Docker Container Infrastructure
Run command in terminal:
```bash
docker compose up --build -d
```
Verify 4 healthy containers running:
```bash
docker ps
```

---

### Step 2: Open OpenAPI / Swagger UI
Open browser to:
```
http://localhost:8000/docs
```
Show interactive endpoints: `POST /ingest`, `POST /chat`, `GET /health`.

---

### Step 3: Upload `customers.csv` via Swagger / curl
Execute upload:
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```
Show HTTP 200 JSON response:
```json
{
  "job_id": "fdde9490-3009-4828-b4ff-ecb410ec7e70",
  "filename": "customers.csv",
  "rows": 20,
  "messages_published": 20,
  "topic": "customer-data",
  "status": "published"
}
```

---

### Step 4: Show Kafka Producer Logs
Show API container streaming logs:
```bash
docker compose logs --tail=25 api
```
*Point out:* `Kafka connected`, `Publishing started`, `messages_published=20`, `Kafka producer closed`.

---

### Step 5: Show Kafka Consumer Logs
Show Loader container real-time logs:
```bash
docker compose logs --tail=25 loader
```
*Point out:* `Received Message | Job ID: ...`, `Received row 1` through `Received row 20`, `Creating Customer Node`, `Customer Inserted`.

---

### Step 6: Open Neo4j Browser
Navigate browser to:
```
http://localhost:7474
```
Login with username `neo4j` and password `changeme`.

---

### Step 7: Verify Node Count in Neo4j Browser
Run Cypher query in Neo4j query editor:
```cypher
MATCH (c:Customer)
RETURN count(c);
```
*Expected Result:* `20` customer nodes created.

---

### Step 8: Open Chatbot Web Interface
Open browser to `ui/index.html` (or `http://localhost:3000`).
Show sidebar, health badge (`API & Neo4j Connected`), and welcome message card.

---

### Step 9: Ask "How many customers are there?"
Type or click preset chip: **"How many customers are there?"**
*Bot Response:* **"There are 20 customers."**

---

### Step 10: Ask "Show customer 1"
Type or click preset chip: **"Show customer 1"**
*Bot Response:* **"Customer 1: Selvaa | Email: selvaa@example.com | City: Coimbatore, India | Age: 22"**

---

### Step 11: Ask "Show customers from Chennai"
Type or click preset chip: **"Show customers from Chennai"**
*Bot Response:* **"Customers from Chennai: Arun (ID: 2)"**

---

### Step 12: Explain Architecture
Conclude demo by explaining the 5-stage decoupled microservice pipeline:
- **CSV Ingestion** -> **Kafka Event Streaming** -> **Async Consumer Worker** -> **Idempotent Cypher MERGE** -> **Sub-50ms Graph Query Backend**.
