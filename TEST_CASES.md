# GraphChatEngine – Comprehensive Test Cases Specification

> 32 Rigorous Test Cases covering API Ingestion, Validation, Kafka Streaming, Consumer Worker, Neo4j Graph Loader, Chat Backend, and Frontend Interface.

---

## Category 1: Infrastructure & Health (TC-01 to TC-04)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-01** | Docker Stack Boot | `docker compose up --build` | 4 healthy containers (`api`, `loader`, `kafka`, `neo4j`) | ✅ PASS |
| **TC-02** | Root Endpoint Probe | `GET /` | `HTTP 200 {"status":"running","service":"api"}` | ✅ PASS |
| **TC-03** | Health Endpoint Probe | `GET /health` | `HTTP 200 {"status":"ok"}` | ✅ PASS |
| **TC-04** | Neo4j Driver Connection | Driver initialization | Connectivity verified without exception | ✅ PASS |

---

## Category 2: CSV Upload & Validation (TC-05 to TC-12)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-05** | Valid Customer CSV | `POST /ingest customers.csv` (20 rows) | `HTTP 200 {"status":"published","messages_published":20}` | ✅ PASS |
| **TC-06** | Valid Employee CSV | `POST /ingest employees.csv` | `HTTP 200 {"status":"published","messages_published":15}` | ✅ PASS |
| **TC-07** | Invalid File Extension | `POST /ingest invalid.txt` | `HTTP 400 {"error":"Only CSV files are supported..."}` | ✅ PASS |
| **TC-08** | Missing File Payload | `POST /ingest` (empty body) | `HTTP 422 Unprocessable Entity` | ✅ PASS |
| **TC-09** | Empty CSV (Headers only)| `POST /ingest empty.csv` | `HTTP 400 {"error":"CSV file contains no data rows..."}` | ✅ PASS |
| **TC-10** | Malformed CSV Format | `POST /ingest invalid.csv` | `HTTP 422 {"error":"Failed to parse CSV..."}` | ✅ PASS |
| **TC-11** | Large CSV Processing | 1,000 row CSV upload | `HTTP 200 messages_published: 1000` | ✅ PASS |
| **TC-12** | Missing Headers CSV | `POST /ingest no_headers.csv` | `HTTP 400` validation error | ✅ PASS |

---

## Category 3: Kafka Producer & Streaming (TC-13 to TC-17)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-13** | Topic Auto-Creation | Produce row to `customer-data` | Topic `customer-data` auto-created | ✅ PASS |
| **TC-14** | Message Partition Keying| Producer `key=job_id` | All job rows assigned to single partition | ✅ PASS |
| **TC-15** | Producer Acks='all' | Record delivery | Producer waits for full broker acknowledgment | ✅ PASS |
| **TC-16** | NaN Values Serialization| DataFrame with NaN values | JSON payload emits `null` cleanly | ✅ PASS |
| **TC-17** | Kafka Broker Downtime | Produce during broker pause | `HTTP 503 Service Unavailable` | ✅ PASS |

---

## Category 4: Kafka Consumer & Loader Worker (TC-18 to TC-22)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-18** | Consumer Subscription | Worker boot | Subscribes to `customer-data` topic | ✅ PASS |
| **TC-19** | JSON Deserialization | Raw bytes payload | Deserialized to dictionary | ✅ PASS |
| **TC-20** | Schema Validation | Payload missing `job_id` | Rejects payload, logs warning, continues | ✅ PASS |
| **TC-21** | Consumer Reconnection | Broker restart | Consumer retries with backoff and reconnects | ✅ PASS |
| **TC-22** | Graceful Shutdown | Container SIGTERM | Consumer closes cleanly (`LeaveGroup`) | ✅ PASS |

---

## Category 5: Neo4j Graph Loader (TC-23 to TC-26)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-23** | Customer Node Creation | Valid record dict | `:Customer` node created in Neo4j | ✅ PASS |
| **TC-24** | Cypher MERGE Idempotency| Re-upload `customers.csv` | Node count remains 20 (updates existing) | ✅ PASS |
| **TC-25** | Key Field Normalization | Payload with `CustomerID`/`id` | `customerId` property mapped cleanly | ✅ PASS |
| **TC-26** | Neo4j Downtime Retry | Write during DB reboot | Repository retries with backoff | ✅ PASS |

---

## Category 6: Chat Backend API (`POST /chat`) (TC-27 to TC-30)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-27** | Count Customers Question| `POST /chat "How many customers are there?"` | `{"answer":"There are 20 customers."}` | ✅ PASS |
| **TC-28** | List Customers Question | `POST /chat "List all customers"` | `{"answer":"Customers:\n1: Selvaa..."}` | ✅ PASS |
| **TC-29** | Single Customer Query | `POST /chat "Show customer 1"` | `{"answer":"Customer 1: Selvaa..."}` | ✅ PASS |
| **TC-30** | City Filter Query | `POST /chat "Show customers from Chennai"` | `{"answer":"Customers from Chennai: Arun..."}` | ✅ PASS |

---

## Category 7: Frontend Interface & Edge Cases (TC-31 to TC-32)

| ID | Title | Input | Expected Output | Status |
|----|-------|-------|-----------------|--------|
| **TC-31** | Unsupported Question | `POST /chat "What is capital of France?"` | `{"answer":"Sorry, I can answer only..."}` | ✅ PASS |
| **TC-32** | Clear Chat Action | Click "Clear Chat" button | Chat log reset, welcome card restored | ✅ PASS |
