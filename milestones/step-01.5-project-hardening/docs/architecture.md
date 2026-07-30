# Architecture – GraphChatEngine

> Component-level architecture documentation for the CSV → Kafka → Neo4j Chatbot pipeline.

---

## High-Level ASCII Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                         HOST MACHINE                                  │
│                                                                       │
│   Browser            curl / Postman          Neo4j Browser           │
│      │                     │                       │                  │
│      │                     │                       │                  │
│   port 8000           port 8000              port 7474 / 7687        │
│      │                     │                       │                  │
│ ─────┼─────────────────────┼───────────────────────┼──── Docker ──── │
│      │                     │                       │                  │
│      ▼                     ▼                       │                  │
│  ┌───────────────────────────┐                     │                  │
│  │      graphchat-api        │                     │                  │
│  │      FastAPI / Uvicorn    │                     │                  │
│  │      python:3.11-slim     │                     │                  │
│  │                           │                     │                  │
│  │  GET  /                   │                     │                  │
│  │  GET  /health             │                     │                  │
│  │  POST /ingest ────────────┼──────────────┐      │                  │
│  │                           │              │      │                  │
│  │  [Milestone 03+]          │              ▼      │                  │
│  └───────────────────────────┘    ┌─────────────────┐                │
│                                   │  graphchat-kafka │                │
│                                   │  apache/kafka    │                │
│                                   │  3.7.0 KRaft     │                │
│                                   │  port 29092 (int)│                │
│                                   │  port 9092 (ext) │                │
│                                   └────────┬─────────┘                │
│                                            │                          │
│                                            ▼                          │
│                                   ┌─────────────────┐                │
│                                   │ graphchat-loader │                │
│                                   │ Python worker    │                │
│                                   │ python:3.11-slim │                │
│                                   │                  │                │
│                                   │ [Milestone 03+]  │                │
│                                   └────────┬─────────┘                │
│                                            │                          │
│                                            ▼                          │
│                                   ┌─────────────────┐                │
│                          ─────────│  graphchat-neo4j │─── ◄ Browser  │
│                                   │  neo4j:5.19      │               │
│                                   │  port 7687 Bolt  │               │
│                                   │  port 7474 HTTP  │               │
│                                   └─────────────────┘                │
│                                                                       │
│  ─────────────────── graphchat-net (Docker bridge) ───────────────── │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### 1. graphchat-api — FastAPI Service

| Property          | Value                                        |
|-------------------|----------------------------------------------|
| **Image**         | Built from `api/Dockerfile` (python:3.11-slim) |
| **Port**          | 8000 (external), 8000 (internal)             |
| **Framework**     | FastAPI 0.111 + Uvicorn 0.29                 |
| **Health Check**  | `python -c "urllib.request.urlopen('http://localhost:8000/health')"` |

**Responsibilities:**
- Expose the REST API at port 8000
- Validate CSV file uploads (extension, size, structure)
- Extract metadata (rows, columns, size) from CSV
- Generate UUID4 job identifiers
- Return structured JSON responses
- *Future:* Produce validated rows to Kafka

**Internal Structure:**
```
api/
├── core/            ← Settings, logging configuration
├── routers/         ← HTTP layer (thin, delegates to services)
├── schemas/         ← Pydantic models (validation + Swagger docs)
├── services/        ← Business logic (CSV validation, metadata)
├── utils/           ← Stateless helper functions
└── main.py          ← App factory (registers routers, middleware)
```

---

### 2. graphchat-kafka — Apache Kafka 3.7 (KRaft Mode)

| Property          | Value                                        |
|-------------------|----------------------------------------------|
| **Image**         | `apache/kafka:3.7.0`                         |
| **Port (external)** | 9092 — for host-machine access             |
| **Port (internal)** | 29092 — for Docker-network traffic         |
| **Mode**          | KRaft (no ZooKeeper)                         |
| **Health Check**  | `kafka-broker-api-versions.sh`               |

**Why KRaft?**
Kafka Raft (KRaft) replaces ZooKeeper as the metadata store. Available since Kafka 2.8, production-stable since 3.3. Benefits:
- One fewer service to manage
- Faster controller elections
- Simpler configuration
- Reduced memory footprint

**Listener configuration:**
```
PLAINTEXT       → kafka:29092    ← used inside Docker network (container-to-container)
PLAINTEXT_HOST  → localhost:9092 ← used from the host machine
CONTROLLER      → kafka:9093     ← used for KRaft controller-broker communication
```

**Future role (Milestone 03):**
Receives messages from the API (`csv-records` topic) and delivers them to the Loader consumer.

---

### 3. graphchat-loader — Internal Worker Service

| Property         | Value                                         |
|------------------|-----------------------------------------------|
| **Image**        | Built from `loader/Dockerfile` (python:3.11-slim) |
| **Port**         | None — internal worker only                   |
| **Health Check** | None (no HTTP interface)                      |

**Current behaviour (Milestone 01.5):**
Prints `"Loader Started..."` and keeps the process alive in a `while True: sleep(60)` loop.

**Future role (Milestone 03+):**
- Subscribe to Kafka topic `csv-records`
- Parse incoming JSON messages
- Write entities and relationships to Neo4j

---

### 4. graphchat-neo4j — Neo4j Community Edition 5.19

| Property          | Value                                        |
|-------------------|----------------------------------------------|
| **Image**         | `neo4j:5.19-community`                       |
| **Port (HTTP)**   | 7474 — Neo4j Browser web UI                  |
| **Port (Bolt)**   | 7687 — Driver connections (Python, Java, etc.) |
| **Health Check**  | `wget http://localhost:7474`                 |

**Why a graph database?**
Relational databases store relationships as foreign-key joins, which require expensive table scans for multi-hop traversals. Neo4j stores relationships as first-class citizens (edges), making queries like "find all products purchased by customers in the same city as Alice" run in constant time relative to the number of hops, not the total number of rows.

**Data model (planned):**
```
(:Customer {id, name, email, city, tier})
  -[:PLACED]->(:Order {order_id, date, total})
  -[:CONTAINS]->(:Product {id, name, category, price})
  -[:LOCATED_IN]->(:City {name})
  -[:COUNTRY]->(:Country {name})
(:Employee {id, name, department})
  -[:REPORTS_TO]->(:Employee)
```

---

## Network Architecture

All four containers share the `graphchat-net` Docker **bridge network**.

```
graphchat-net (172.x.x.x/16)
├── graphchat-api     → can reach kafka:29092, neo4j:7687
├── graphchat-kafka   → can reach api:8000, loader:* (no HTTP)
├── graphchat-loader  → can reach kafka:29092, neo4j:7687
└── graphchat-neo4j   → passively receives driver connections
```

**Key design decision:** Services communicate using Docker's internal DNS (service name = hostname). The API uses `kafka:29092`, not `localhost:9092`. This is why two listener addresses are configured on Kafka.

---

## Startup Order

```
┌──────────┐    ┌──────────┐
│  kafka   │    │  neo4j   │
│ (healthy)│    │ (healthy)│
└────┬─────┘    └────┬─────┘
     │               │
     └───────┬────────┘
             │  depends_on: condition: service_healthy
             ▼
     ┌───────────────┐     ┌──────────────┐
     │      api      │     │    loader    │
     │   (starts)    │     │   (starts)   │
     └───────────────┘     └──────────────┘
```

The `depends_on: condition: service_healthy` directive in `docker-compose.yml` ensures the API and Loader only start after Kafka and Neo4j pass their health checks. This prevents connection-refused errors during startup.

---

## Data Flow (Full Pipeline — Milestone 05 Target)

```
1. User uploads CSV via browser or curl
          │
          ▼
2. POST /ingest (FastAPI)
   ├── Validate file extension (.csv)
   ├── Check file not empty
   ├── Parse with pandas
   ├── Validate structure (headers, rows)
   ├── Extract metadata (rows, columns, size_kb)
   ├── Generate UUID4 job_id
   └── Return 200 OK with metadata JSON
          │
          │ [Milestone 03]
          ▼
3. Kafka Producer (API)
   └── Produce each row as JSON → topic: csv-records
          │
          ▼
4. Kafka Consumer (Loader)
   └── Read messages from csv-records
          │
          │ [Milestone 04]
          ▼
5. Neo4j Writer (Loader)
   └── Create nodes and relationships with Cypher MERGE
          │
          │ [Milestone 05]
          ▼
6. Chatbot Query (API)
   ├── Parse natural-language question
   ├── Generate Cypher query
   ├── Execute against Neo4j
   └── Return human-readable answer
```
