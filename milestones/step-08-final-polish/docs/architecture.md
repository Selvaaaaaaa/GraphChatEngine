# GraphChatEngine – Complete System Architecture Document

> Comprehensive technical architecture blueprint covering system components, end-to-end data flow, stream processing, graph database schema, and component responsibilities.

---

## 1. System Overview & Architectural Diagram

GraphChatEngine is an event-driven, microservice-inspired data processing and knowledge graph chatbot pipeline built with Python 3.11, FastAPI, Apache Kafka 3.7 (KRaft mode), and Neo4j Community 5.19.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   DOCKER NETWORK: graphchat-net                             │
│                                                                                             │
│  ┌───────────────────────┐          ┌───────────────────────┐    ┌───────────────────────┐  │
│  │   Browser UI Client   │          │   FastAPI API Engine  │    │  Kafka Broker (KRaft) │  │
│  │  (ui/index.html / JS) │          │     (api/main.py)     │    │  (apache/kafka:3.7)   │  │
│  └───────────┬───────────┘          └───────────┬───────────┘    └───────────┬───────────┘  │
│              │                                  │                            │              │
│              │ (HTTP POST /ingest)              │ (Produce Row JSONs)        │              │
│              ├─────────────────────────────────►│───────────────────────────►│              │
│              │                                  │                            │              │
│              │ (HTTP POST /chat)                │                            │ (Consume)    │
│              ├─────────────────┐                │                            ▼              │
│              │                 │                │               ┌────────────────────────┐  │
│              │                 │                │               │ Loader Worker Service  │  │
│              │                 │                │               │ (loader/consumer.py)   │  │
│              │                 │                │               └────────────┬───────────┘  │
│              │                 │                │                            │              │
│              │                 │                │                            │ (MERGE)      │
│              │                 ▼                │                            ▼              │
│              │       ┌──────────────────┐       │               ┌────────────────────────┐  │
│              └──────►│ Neo4j Repository │◄──────┴───────────────┤ Neo4j Graph Database   │  │
│                      │ (Read Queries)   │                       │ (neo4j:5.19-community) │  │
│                      └──────────────────┘                       └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End Data Flow

```
CSV File ──► POST /ingest ──► Pandas Validation ──► Kafka Producer ──► Topic: customer-data
                                                                            │
                                                                            ▼
Chat Output ◄── Chat Service ◄── Neo4j Repository ◄── Cypher MERGE ◄── Kafka Consumer
```

### Stage 1: Ingestion & Validation (`api/services/ingest_service.py`)
- User submits multipart CSV upload to `POST /ingest`.
- Primary guard verifies file extension `.csv`.
- pandas parses bytes, validating headers, empty files, and malformed rows.
- UUID4 `job_id` is assigned.
- DataFrame rows are converted to JSON-compatible Python dictionaries (`NaN -> None`).

### Stage 2: Streaming (`api/services/kafka_producer.py`)
- `KafkaProducer` connects to `kafka:29092` with `acks='all'` and `retries=3`.
- Each row payload is wrapped in a structured envelope: `{job_id, row_number, timestamp, data}`.
- Message key is set to `job_id` ensuring all rows from one upload land in the same partition for ordered delivery.
- Producer calls `flush()` to guarantee transmission before returning HTTP response `status: "published"`.

### Stage 3: Real-Time Consumption (`loader/services/kafka_consumer.py`)
- `KafkaConsumer` worker in `loader` connects to `kafka:29092` using consumer group `graphchat-loader-group`.
- Polls topic `customer-data` using `auto_offset_reset='earliest'`.
- Safely deserializes UTF-8 JSON payloads and validates required fields (`job_id`, `row_number`, `timestamp`, `data`).
- Isolates errors to prevent malformed messages from terminating the worker thread.

### Stage 4: Knowledge Graph Ingestion (`loader/services/neo4j_repository.py` & `graph_loader.py`)
- `GraphLoader` delegates row data to `Neo4jRepository`.
- Official `neo4j` Python driver connects to `bolt://neo4j:7687`.
- Executes Cypher `MERGE (c:Customer {customerId: $CustomerID}) SET ...` query to insert/update customer nodes idempotently.

### Stage 5: Graph Query & Chat Execution (`api/chat/`)
- User posts question to `POST /chat`.
- `QueryMapper` maps supported questions to Cypher templates (`MATCH (c:Customer)...`).
- `Neo4jChatRepository` executes read query and returns records.
- `ChatService` formats answer string and logs execution timing (ms) and record counts.

---

## 3. Component Responsibilities

| Component | Module Location | Primary Responsibility |
|-----------|-----------------|------------------------|
| **Ingest Router** | `api/routers/ingest.py` | Parses multipart file uploads; maps validation & Kafka errors to HTTP responses |
| **Ingest Service** | `api/services/ingest_service.py` | Runs pandas structural validation; converts rows to dicts |
| **Kafka Producer** | `api/services/kafka_producer.py` | Serializes JSON messages; publishes to Kafka with `acks='all'` |
| **Kafka Consumer** | `loader/services/kafka_consumer.py` | Polls `customer-data` topic; validates message envelopes; error resilience |
| **Graph Loader** | `loader/services/graph_loader.py` | Service layer orchestrating graph loading tasks |
| **Neo4j Repository (Write)** | `loader/services/neo4j_repository.py` | Executes Cypher `MERGE` statements via Bolt protocol |
| **Chat Router** | `api/chat/controller.py` | Exposes `POST /chat`; handles HTTP response codes |
| **Chat Service** | `api/chat/service.py` | Measures execution timing; logs query metrics; formats answers |
| **Query Mapper** | `api/chat/query_mapper.py` | Maps predefined questions to Cypher queries |
| **Neo4j Repository (Read)** | `api/chat/repository.py` | Executes Cypher read queries against Neo4j |
| **Frontend UI** | `ui/index.html`, `style.css`, `app.js` | ChatGPT-style glassmorphic interface |

---

## 4. Security & Error Boundary Architecture

- **Zero Cypher Injection:** All Cypher queries use parameterized inputs (`$CustomerID`, `$city`). No raw string formatting is ever executed in Cypher.
- **Fail-Safe Pipeline:** Producer or Consumer failures in single records log explicit warnings without stopping the service loops.
- **Isolated Clean Architecture:** Routers contain zero business logic and zero database queries. Repositories handle database connectivity exclusively.
