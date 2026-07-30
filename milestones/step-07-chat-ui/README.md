# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built incrementally during a software hackathon.

[![Status](https://img.shields.io/badge/milestone-07%20chat%20ui-green)]()
[![Python](https://img.shields.io/badge/python-3.11-green)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)]()
[![Kafka](https://img.shields.io/badge/Kafka-3.7%20KRaft-orange)]()
[![Neo4j](https://img.shields.io/badge/Neo4j-5.19%20Community-purple)]()

---

## Overview

GraphChatEngine is a production-style, containerised pipeline that:

1. **Ingests** CSV files through a validated REST API (`POST /ingest`)
2. **Streams** rows through Apache Kafka (Milestone 03)
3. **Consumes** & validates messages in real-time worker (Milestone 04)
4. **Stores** entities in Neo4j graph database using Cypher `MERGE` (Milestone 05)
5. **Queries** Neo4j knowledge graph via deterministic backend (`POST /chat`) (Milestone 06)
6. **Presents** an interactive ChatGPT-style frontend UI (Milestone 07)

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

---

## Frontend Chat Interface (Milestone 07)

### Features
- **ChatGPT-Style Experience:** Responsive dark glassmorphism design with rounded message bubbles, avatar icons, and timestamps.
- **Sidebar & Preset Chips:** Quick preset question chips ("How many customers are there?", "List all customers", etc.) that trigger instant queries.
- **Live Health Status:** Continuous health monitoring connecting to `http://localhost:8000/health`.
- **Loading & Typing Indicators:** Smooth animated typing indicators while awaiting backend API responses.
- **Error Resiliency:** User-friendly error bubbles handling backend disconnects, timeouts, and server exceptions gracefully.

### How to Run Frontend

1. Ensure the Docker containers are running:
```bash
docker compose up --build -d
```

2. Open `ui/index.html` in any web browser, or serve via standard local HTTP server:
```bash
# Option A: Double click ui/index.html in File Explorer
# Option B: Run Python simple server
python -m http.server 3000 --directory ui
```
Then visit `http://localhost:3000`.

---

## Screenshots

1. **Frontend Welcome Screen:** Sidebar with pipeline status, preset chips, and bot welcome message.
2. **Chat Conversation:** User and Bot bubbles showing real-time query responses ("There are 20 customers.").
3. **Swagger API UI (`http://localhost:8000/docs`):** OpenAPI interactive endpoints for `/ingest` and `/chat`.

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
| 06    | Graph Query Backend     | ✅ Complete |
| 07    | Frontend Chat Interface | ✅ Complete |

---

## License

MIT
