# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built incrementally during a software hackathon.

[![Status](https://img.shields.io/badge/status-hackathon--submission--ready-success)]()
[![Python](https://img.shields.io/badge/python-3.11-green)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)]()
[![Kafka](https://img.shields.io/badge/Kafka-3.7%20KRaft-orange)]()
[![Neo4j](https://img.shields.io/badge/Neo4j-5.19%20Community-purple)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## Project Overview

GraphChatEngine is a production-style, multi-container data processing and knowledge graph chatbot pipeline that converts raw CSV business data into an interactive conversational interface.

### End-to-End Pipeline Workflow
```
CSV Upload ──► FastAPI Ingestion ──► Kafka Producer ──► Topic: customer-data
                                                              │
                                                              ▼
Chat UI ◄── Chat API Backend ◄── Neo4j Graph DB ◄── Cypher MERGE ◄── Kafka Consumer
```

1. **Ingest (`POST /ingest`):** Validates CSV structure, headers, and encoding using pandas; extracts metadata.
2. **Stream (Kafka Producer):** Converts rows into JSON event messages published to Kafka topic `customer-data`.
3. **Process (Kafka Consumer):** Async worker polls Kafka, deserializes JSON, and validates message schemas.
4. **Store (Neo4j Graph Loader):** Executes idempotent Cypher `MERGE` statements to build `:Customer` graph nodes without duplicates.
5. **Query (Chat Backend `POST /chat`):** Maps natural language questions to deterministic Cypher queries with sub-50ms execution times and zero AI hallucinations.
6. **Interact (Frontend UI):** ChatGPT-style glassmorphic interface with preset chips, auto-scrolling, typing animations, and health probes.

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Web Framework** | FastAPI | 0.111.0 | REST API (`/ingest`, `/chat`, `/health`) |
| **ASGI Server** | Uvicorn | 0.29.0 | ASGI web server runtime |
| **Data Validation** | pandas | 2.2.2 | CSV parsing & validation |
| **Event Streaming** | Apache Kafka | 3.7.0 (KRaft) | Message broker in ZooKeeper-less KRaft mode |
| **Kafka Driver** | kafka-python | 2.0.2 | Producer and Consumer Python library |
| **Graph Database** | Neo4j Community | 5.19.0 | Native graph database |
| **Graph Driver** | neo4j | 5.19.0 | Official Bolt protocol driver |
| **Orchestration** | Docker Compose | 2.x | Multi-container service management |
| **Frontend UI** | HTML5 / CSS3 / Vanilla JS | Standard | Dark glassmorphism chatbot UI |

---

## Project Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │           Docker Network: graphchat-net       │
                        │                                               │
  Browser UI / curl ───►│  ┌─────────┐    ┌─────────┐                 │
  (ui/index.html)       │  │   API   │───►│  Kafka  │                 │
     │                  │  │ :8000   │    │  :9092  │                 │
     │ (POST /chat)     │  │ FastAPI │    │  KRaft  │                 │
     └─────────────────►│  └────┬────┘    └────┬────┘                 │
                        │       │              │                      │
                        │       │         ┌────▼────┐                 │
                        │       │         │ Loader  │                 │
                        │       │         │ Worker  │                 │
                        │       │         └────┬────┘                 │
                        │       │              │ (Graph Loader /      │
                        │       │              │  Neo4j Repository)   │
                        │       │         ┌────▼────┐                 │
                        │       └────────►│  Neo4j  │                 │
                        │                 │  :7474  │                 │
                        │                 │  :7687  │                 │
                        │                 └─────────┘                 │
                        └─────────────────────────────────────────────┘
```

Detailed architecture diagrams and data flows are documented in [docs/ARCHITECTURE.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/docs/ARCHITECTURE.md).

---

## Installation & Running the Project

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.x
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x

### Quick Start (Single Command)

```bash
# 1. Clone the repository
git clone https://github.com/Selvaaaaaaa/GraphChatEngine.git
cd GraphChatEngine

# 2. Copy environment configuration template
cp .env.example .env

# 3. Start all services in detached mode
docker compose up --build -d
```

Verify service health:
```bash
docker ps
```
*Expected output: All 4 containers (`graphchat-api`, `graphchat-loader`, `graphchat-kafka`, `graphchat-neo4j`) in Healthy status.*

---

## Service Endpoints & Verification

| Service | Protocol | Host URL | Description |
|---------|----------|----------|-------------|
| **Swagger UI** | HTTP | `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| **Chat API** | HTTP | `POST http://localhost:8000/chat` | Natural language graph query endpoint |
| **CSV Ingest API** | HTTP | `POST http://localhost:8000/ingest` | CSV upload & streaming endpoint |
| **API Health Probe** | HTTP | `GET http://localhost:8000/health` | Health check endpoint |
| **Neo4j Browser UI** | HTTP | `http://localhost:7474` | Database graphical interface (user: `neo4j`, password: `changeme`) |
| **Neo4j Bolt Protocol** | Bolt | `bolt://localhost:7687` | Native driver port |
| **Kafka Broker** | TCP | `localhost:9092` | External broker access |
| **Frontend Web App** | Static | Open `ui/index.html` in browser | ChatGPT-style web UI |

---

## Usage Guide

### 1. Ingest CSV Data via REST API
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```
*Response:*
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

### 2. Query Knowledge Graph via Chat API
```bash
curl.exe -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"How many customers are there?"}'
```
*Response:*
```json
{
  "answer": "There are 20 customers."
}
```

### 3. Open Frontend Chat Interface
Open `ui/index.html` in any web browser or serve via Python local server:
```bash
python -m http.server 3000 --directory ui
```
Visit `http://localhost:3000` to interact with the chatbot.

---

## Supported Questions Matrix

| Question | Generated Cypher |
|----------|------------------|
| **How many customers are there?** | `MATCH (c:Customer) RETURN count(c)` |
| **List all customers** | `MATCH (c:Customer) RETURN c.customerId, c.name, c.city ORDER BY toInteger(c.customerId)` |
| **Show customer 1** | `MATCH (c:Customer {customerId: 1}) RETURN c` |
| **Show customers from Chennai** | `MATCH (c:Customer) WHERE toLower(c.city) = "chennai" RETURN c` |
| **Show customers from Coimbatore** | `MATCH (c:Customer) WHERE toLower(c.city) = "coimbatore" RETURN c` |
| **Show all emails** | `MATCH (c:Customer) RETURN c.email` |
| **Show all cities** | `MATCH (c:Customer) RETURN DISTINCT c.city` |

---

## Common Errors & Troubleshooting

| Symptom / Error | Root Cause | Resolution |
|-----------------|------------|------------|
| `API container shows unhealthy` | wget/curl missing in python-slim image | Fixed — Health check uses Python `urllib` probe |
| `Port conflict (8000, 7474, 9092)` | Another service is listening on port | Stop local Kafka/Neo4j/FastAPI instances or edit `docker-compose.yml` |
| `NoBrokersAvailable` in producer | Kafka broker still initializing | Handled — Retry logic with backoff auto-reconnects |
| `JSONDecodeError` on consumer | Invalid non-JSON bytes in topic | Handled — Consumer rejects bad messages without terminating |

---

## Documentation Index

- **System Architecture:** [docs/ARCHITECTURE.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/docs/ARCHITECTURE.md)
- **Final Project Report:** [REPORT_FINAL.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/REPORT_FINAL.md)
- **Pitch & Presentation Notes:** [PRESENTATION_NOTES.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/PRESENTATION_NOTES.md)
- **50 Technical Viva Q&As:** [VIVA_FINAL.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/VIVA_FINAL.md)
- **Step-by-Step Demo Script:** [DEMO_SCRIPT.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/DEMO_SCRIPT.md)
- **32 Test Cases Specification:** [TEST_CASES.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/TEST_CASES.md)
- **Verification Matrix:** [FINAL_VERIFICATION.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/FINAL_VERIFICATION.md)
- **Project Structure Reference:** [PROJECT_STRUCTURE.md](file:///p:/CodeVerse/Projects%20Space/GraphChatEngine/PROJECT_STRUCTURE.md)

---

## License

MIT
