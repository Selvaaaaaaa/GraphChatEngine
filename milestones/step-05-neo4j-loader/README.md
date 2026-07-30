# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built incrementally during a software hackathon.

[![Status](https://img.shields.io/badge/milestone-05%20neo4j%20loader-green)]()
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
4. **Stores** entities in Neo4j graph database using Cypher MERGE (Milestone 05)
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
                        │                 │ Worker  │                 │
                        │                 └────┬────┘                 │
                        │                      │ (Graph Loader /      │
                        │                      │  Neo4j Repository)   │
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
3. Loader Consumer reads from Kafka → calls `GraphLoader` → `Neo4jRepository`
4. `Neo4jRepository` executes Cypher `MERGE` → stores `:Customer` nodes in Neo4j

---

## Folder Structure

```
GraphChatEngine/
├── api/                        # FastAPI application (Python)
│   ├── core/
│   │   ├── config.py           # Settings from env vars
│   │   └── logging_config.py   # Root logger setup
│   ├── routers/
│   │   └── ingest.py           # POST /ingest HTTP handler
│   ├── schemas/
│   │   └── ingest.py           # Pydantic models
│   ├── services/
│   │   ├── ingest_service.py   # Validation & orchestration
│   │   └── kafka_producer.py   # Kafka producer service
│   ├── utils/
│   │   └── file_helpers.py     # Helpers
│   ├── main.py                 # App factory
│   ├── requirements.txt
│   └── Dockerfile
├── loader/                     # Internal worker service (Python)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py   # Kafka consumer service
│   │   ├── graph_loader.py     # Graph loader orchestration service
│   │   └── neo4j_repository.py # Neo4j Cypher execution repository
│   ├── consumer.py             # Main consumer execution entrypoint
│   ├── loader.py               # Loader service delegate
│   ├── requirements.txt
│   └── Dockerfile
├── ui/                         # Static browser UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample-data/                # Test CSV files
│   └── customers.csv           # 20-row customer dataset
├── docs/
│   ├── architecture.md         # Architecture documentation
│   ├── VIVA_MILESTONE_01.md    # Foundation viva Q&As
│   ├── REPORT_MILESTONE_01.md  # Foundation report
│   ├── VIVA_MILESTONE_03.md    # Kafka producer viva Q&As
│   ├── REPORT_MILESTONE_03.md  # Kafka producer report
│   ├── VIVA_MILESTONE_04.md    # Kafka consumer viva Q&As
│   ├── REPORT_MILESTONE_04.md  # Kafka consumer report
│   ├── VIVA_MILESTONE_05.md    # Neo4j Graph Loader viva Q&As
│   └── REPORT_MILESTONE_05.md  # Neo4j Graph Loader report
├── milestones/                 # Immutable snapshots per milestone
│   ├── step-01-project-foundation/
│   ├── step-01.5-project-hardening/
│   ├── step-02-csv-upload/
│   ├── step-03-kafka-producer/
│   ├── step-04-kafka-consumer/
│   └── step-05-neo4j-loader/
├── docker-compose.yml
├── .env.example                # Environment variables reference
├── TESTING.md                  # Test execution guide
└── README.md
```

---

## Neo4j Graph Loader (Milestone 05)

### Graph Architecture

Messages consumed from Kafka topic `customer-data` are processed through `GraphLoader` and stored in Neo4j as `:Customer` nodes using Cypher `MERGE` semantics.

```
Kafka Payload ──► GraphLoader ──► Neo4jRepository ──► (:Customer {customerId, name, city, state, country, age, email, phone})
```

### Cypher Queries

```cypher
// Upsert Customer node (prevents duplicates)
MERGE (c:Customer {customerId: $CustomerID})
SET c.name = $Name,
    c.city = $City,
    c.state = $State,
    c.country = $Country,
    c.age = $Age,
    c.email = $Email,
    c.phone = $Phone
RETURN c
```

---

## How to Verify

1. **Upload CSV via API:**
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```

2. **Verify Node Count in Neo4j Browser (`http://localhost:7474`) or via CLI:**
```cypher
MATCH (c:Customer)
RETURN count(c);
```
*Expected Output:* `20`

3. **Inspect Sample Nodes:**
```cypher
MATCH (c:Customer)
RETURN c
LIMIT 5;
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
| 05    | Neo4j Graph Loader      | ✅ Complete |
| 06    | Chatbot / NLP Interface | 🔜 Planned  |

---

## License

MIT
