# REPORT NOTES – Milestone 05: Neo4j Graph Loader

> Detailed report documentation for Milestone 05 covering architecture, Cypher graph design, implementation, verification results, screenshots required, and future improvements.

---

## Objective

The objective of Milestone 05 was to connect the Kafka Consumer worker service to Neo4j Graph Database by creating a robust **Graph Loader Service** (`services/graph_loader.py`) and **Neo4j Repository** (`services/neo4j_repository.py`).

Incoming CSV row messages published to Kafka topic `customer-data` are consumed, validated, and automatically upserted into Neo4j as `:Customer` nodes using idempotent Cypher `MERGE` queries.

---

## Architecture & Data Flow

```
┌─────────────────┐       ┌─────────────────┐       ┌────────────────────────┐
│   FastAPI API   │ ────► │  Kafka Broker   │ ────► │ Loader Consumer        │
│ (POST /ingest)  │       │ (customer-data) │       │ (loader/consumer.py)   │
└─────────────────┘       └─────────────────┘       └───────────┬────────────┘
                                                                │
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │ GraphLoader            │
                                                    │ (services/graph_loader)│
                                                    └───────────┬────────────┘
                                                                │
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │ Neo4j Repository       │
                                                    │ (neo4j_repository.py)  │
                                                    └───────────┬────────────┘
                                                                │
                                                                ▼
                                                    ┌────────────────────────┐
                                                    │ Neo4j Database         │
                                                    │ (:Customer Nodes)      │
                                                    └────────────────────────┘
```

---

## Cypher Design

### Node Label & Properties

- **Label:** `:Customer`
- **Primary Key / Identifier:** `customerId`
- **Properties:** `name`, `city`, `state`, `country`, `age`, `email`, `phone`

### Cypher Upsert Query (`MERGE`)

```cypher
MERGE (c:Customer {customerId: $CustomerID})
SET c.name = $Name,
    c.city = $City,
    c.state = $State,
    c.country = $Country,
    c.age = $Age,
    c.email = $Email,
    c.phone = $Phone
RETURN c.customerId AS customerId
```

**Why MERGE?**
`MERGE` ensures idempotency: re-running CSV ingestion or re-consuming Kafka messages updates existing customer nodes rather than creating duplicate graph entities.

---

## Code Structure

- **`loader/services/neo4j_repository.py`**: Handles Neo4j driver initialization, Bolt protocol connections (`bolt://neo4j:7687`), connection retry logic, and parameterized Cypher `MERGE` query execution.
- **`loader/services/graph_loader.py`**: High-level graph loading service that receives record payloads from the Kafka consumer, logs operations (`Creating Customer Node`, `Customer Inserted`, `Graph Loader Success`), and handles errors without interrupting the consumer.
- **`loader/services/kafka_consumer.py`**: Delegates validated message payloads directly to `GraphLoader.process_record()`.

---

## Testing & Verification Results

### Test Execution

1. Upload `sample-data/customers.csv` (20 rows) via REST API:
```bash
curl.exe -X POST http://localhost:8000/ingest -F "file=@sample-data/customers.csv"
```
*API Output:* `{"job_id":"...","rows":20,"messages_published":20,"topic":"customer-data","status":"published"}`

2. Verify Node Count in Neo4j via Cypher:
```cypher
MATCH (c:Customer) RETURN count(c) AS count
```
*Verification Result:* `20`

3. Verify Idempotency / Duplicate Handling:
Re-uploaded `customers.csv` a second time.
*Verification Result:* `Customer Node Count in Neo4j after duplicate upload: 20` (No duplicate nodes created).

4. Retrieve Sample Customer Nodes:
```cypher
MATCH (c:Customer) RETURN c LIMIT 5
```
*Sample Output:*
```json
{"customerId": 1, "name": "Alice Johnson", "city": "New York", "country": "USA", "age": 29, "email": "alice.johnson@example.com"}
{"customerId": 2, "name": "Bob Smith", "city": "London", "country": "UK", "age": 34, "email": "bob.smith@example.com"}
...
```

---

## Screenshots to Capture

1. **Loader Container Log**: Logs displaying `Neo4j Connected`, `Creating Customer Node`, `Customer Inserted`, and `Graph Loader Success`.
2. **Neo4j Browser Query (`MATCH (c:Customer) RETURN count(c)`)**: Graph UI showing count result `20`.
3. **Neo4j Browser Graph Visualizer (`MATCH (c:Customer) RETURN c LIMIT 5`)**: Visual graph bubbles for customer nodes.
4. **Terminal Execution**: `POST /ingest` response and Python Cypher count output.

---

## Future Improvements (Milestone 06+)

- **Relationship Ingestion:** Extend `GraphLoader` to automatically infer and create graph edges (e.g. `(:Customer)-[:LOCATED_IN]->(:City)` and `(:Customer)-[:PLACED]->(:Order)`).
- **Batch Transaction Writing:** Batch multiple Kafka records per Neo4j transaction session for enhanced throughput on multi-gigabyte datasets.
- **Cypher Schema Constraints:** Automatically create Neo4j unique property constraints on startup (`CREATE CONSTRAINT FOR (c:Customer) REQUIRE c.customerId IS UNIQUE`).
