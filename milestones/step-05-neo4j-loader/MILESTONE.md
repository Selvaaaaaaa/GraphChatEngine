# Milestone 05 – Neo4j Graph Loader

## Objective

Implement a Neo4j Graph Loader service (`loader/services/graph_loader.py` and `loader/services/neo4j_repository.py`) that connects to Neo4j Graph Database via the Bolt protocol, receives streamed CSV row payloads from the Kafka Consumer, and upserts them into Neo4j as `:Customer` nodes using Cypher `MERGE` queries.

---

## Features Completed

- ✅ **`loader/services/neo4j_repository.py`** — Handles Neo4j driver connection pooling, auto-retry logic, and parameterized Cypher `MERGE` query execution.
- ✅ **`loader/services/graph_loader.py`** — Service layer orchestrating graph node creation and handling errors safely without interrupting consumer stream.
- ✅ **`loader/services/kafka_consumer.py`** — Integrated with `GraphLoader` to automatically delegate incoming message payloads to Neo4j.
- ✅ **`loader/requirements.txt`** — Added `neo4j==5.19.0`.
- ✅ **`README.md`** — Updated with Neo4j Graph Loader section, graph architecture, Cypher queries, and verification instructions.
- ✅ **`docs/VIVA_MILESTONE_05.md`** — 20 professional viva Q&As.
- ✅ **`docs/REPORT_MILESTONE_05.md`** — Complete milestone report.

---

## What Works

| Feature | Status | Notes |
|---------|--------|-------|
| Neo4j Driver Connection | ✅ | Connects via `bolt://neo4j:7687` with retry |
| Cypher `MERGE` Execution | ✅ | Inserts `:Customer` nodes idempotently |
| Field Normalization | ✅ | Normalizes parameter keys (`CustomerID`, `id`, `Name`, etc.) |
| End-to-End Pipeline Ingestion | ✅ | CSV Upload → Kafka → Consumer → Neo4j |
| Duplicate Node Handling | ✅ | Re-uploading CSV updates existing nodes (count stays 20) |
| Fault Tolerance | ✅ | Failed node insertion logged without stopping consumer |

---

## Verification Results

- **CSV Upload:** `POST /ingest` with `sample-data/customers.csv` (20 rows) → `messages_published: 20`
- **Neo4j Node Count:** `MATCH (c:Customer) RETURN count(c)` → **`20`**
- **Idempotency Verification:** Re-uploading `customers.csv` → count remains **`20`**
