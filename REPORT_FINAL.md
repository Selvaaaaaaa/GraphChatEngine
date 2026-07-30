# GraphChatEngine – Final Project Report

> **Hackathon Final Submission Report**  
> **Project Name:** GraphChatEngine  
> **Tech Stack:** Python 3.11, FastAPI, Apache Kafka 3.7 (KRaft), Neo4j Community 5.19, Docker Compose, Vanilla JS/CSS  

---

## 1. Executive Summary & Problem Statement

Modern enterprise data architectures suffer from data silos: tabular business data stored in CSV files or SQL databases is difficult to query using natural language, and traditional relational databases degrade in performance when querying complex interconnected relationships.

**GraphChatEngine** solves this by providing a complete, containerized, real-time data pipeline that ingests tabular CSV files, streams rows through Apache Kafka, builds a graph knowledge database in Neo4j using idempotent Cypher `MERGE` queries, and provides a deterministic, zero-hallucination chatbot interface.

---

## 2. Project Objectives & Milestones Completed

- ✅ **Milestone 01 — Infrastructure:** Multi-container Docker Compose setup with Python 3.11, FastAPI, Kafka KRaft, Neo4j, and custom Python health checks.
- ✅ **Milestone 01.5 — Project Hardening:** Strict error handling, zero-dependency health checks, test data fixtures, architecture docs, and viva notes.
- ✅ **Milestone 02 — CSV Ingestion & Validation:** REST API `POST /ingest` validating CSV structure, headers, MIME types, and extracting metadata.
- ✅ **Milestone 03 — Kafka Producer:** Dedicated service module converting CSV rows to JSON messages published to `customer-data` topic with `acks='all'`.
- ✅ **Milestone 04 — Kafka Consumer:** Resilient background worker in `loader` subscribing to Kafka, deserializing JSON, validating schema, and logging reception metrics.
- ✅ **Milestone 05 — Neo4j Graph Loader:** Idempotent Cypher `MERGE` graph loader building `:Customer` nodes in Neo4j with duplicate prevention.
- ✅ **Milestone 06 — Graph Query Backend:** Deterministic `POST /chat` backend querying Neo4j via predefined Cypher mappings without AI hallucination.
- ✅ **Milestone 07 — Frontend Chat Interface:** Modern ChatGPT-style glassmorphic UI with responsive sidebar, preset chips, typing indicators, auto-scroll, and console logging.
- ✅ **Milestone 08 — Final Polish & Verification:** Complete end-to-end testing, documentation suite, demo script, test cases, and presentation assets.

---

## 3. Technology Stack Matrix

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **API Web Framework** | FastAPI | 0.111.0 | REST API endpoints (`/ingest`, `/chat`, `/health`) |
| **ASGI Server** | Uvicorn | 0.29.0 | High-performance web server |
| **Data Processing** | pandas | 2.2.2 | CSV parsing and structural validation |
| **Message Streaming** | Apache Kafka | 3.7.0 KRaft | High-throughput distributed event streaming broker |
| **Kafka Client** | kafka-python | 2.0.2 | Producer and Consumer Python library |
| **Graph Database** | Neo4j Community | 5.19.0 | Native graph database storing entities & edges |
| **Graph Client** | neo4j driver | 5.19.0 | Official Bolt protocol database driver |
| **Containerization** | Docker & Compose | 24.x / 2.x | Microservice orchestration and container runtime |
| **Frontend** | Vanilla JS, CSS3, HTML5 | Standard | ChatGPT-style glassmorphic chat interface |

---

## 4. End-to-End Test & Verification Results

| Pipeline Test | Expected Result | Actual Result | Status |
|---------------|-----------------|---------------|--------|
| API Health Check | `{"status":"ok"}` | `{"status":"ok"}` | ✅ PASS |
| Upload `customers.csv` (20 rows) | HTTP 200, `messages_published: 20` | HTTP 200, `messages_published: 20` | ✅ PASS |
| Kafka Message Streaming | 20 JSON messages in `customer-data` | 20 messages verified in topic | ✅ PASS |
| Kafka Consumer Processing | 20 rows consumed & validated | 20 `Received row X` logs | ✅ PASS |
| Neo4j Graph Ingestion | `MATCH (c:Customer) RETURN count(c)` = 20 | `20` customer nodes created | ✅ PASS |
| Duplicate Handling Test | Re-upload `customers.csv` -> count stays 20 | Count remained `20` (MERGE verified) | ✅ PASS |
| Chat `How many customers are there?` | `{"answer":"There are 20 customers."}` | `{"answer":"There are 20 customers."}` | ✅ PASS |
| Chat `Show customer 1` | Details for Selvaa (Coimbatore) | Correct customer details returned | ✅ PASS |
| Unsupported Question | Fallback text | `"Sorry, I can answer only questions..."` | ✅ PASS |
| Frontend Interface | Renders bubbles, chips, typing status | All UI features working | ✅ PASS |

---

## 5. Required Screenshots

1. **`docker ps` Terminal Output:** Showing `graphchat-api`, `graphchat-loader`, `graphchat-kafka`, and `graphchat-neo4j` in healthy status.
2. **Swagger UI (`http://localhost:8000/docs`):** Displays OpenAPI endpoints for `/ingest`, `/chat`, and status checks.
3. **Kafka Logs:** `docker compose logs api` showing `Kafka connected` and `Published row X` entries.
4. **Loader Worker Logs:** `docker compose logs loader` showing `Received Message`, `Creating Customer Node`, and `Customer Inserted`.
5. **Neo4j Browser (`http://localhost:7474`):** Visual graph bubbles for `:Customer` nodes resulting from `MATCH (c:Customer) RETURN c LIMIT 5`.
6. **Frontend Chat Interface:** Full ChatGPT-style UI with conversation log and preset query chips.

---

## 6. Conclusion & Future Scope

GraphChatEngine successfully demonstrates a production-grade, containerized real-time data ingestion and graph chatbot pipeline built incrementally with zero technical debt.

**Future Extensions:**
- **Automated Relationship Extraction:** Automatically infer and map graph edges (e.g. `(:Customer)-[:PLACED]->(:Order)`).
- **Multi-Tenant User Sessions:** Add JWT authentication for multi-tenant data pipelines.
- **Dynamic Schema Graph RAG:** Combine Cypher query generation with local LLMs for arbitrary multi-hop graph questions.
