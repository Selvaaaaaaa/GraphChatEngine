# Milestone 06 – Graph Query API and Chat Backend

## Objective

Create a deterministic, clean-architecture Chatbot Backend (`POST /chat`) that queries the Neo4j Knowledge Graph using predefined Cypher pattern mappings without external AI dependencies, hallucination, or third-party LLMs.

---

## Features Completed

- ✅ **`api/chat/controller.py`** — HTTP controller router (`POST /chat`) with OpenAPI/Swagger documentation.
- ✅ **`api/chat/service.py`** — Service layer orchestrating mapping, query execution, execution timing, and response formatting.
- ✅ **`api/chat/query_mapper.py`** — Query mapper defining predefined Cypher queries for supported questions and fallback handling for unsupported questions.
- ✅ **`api/chat/repository.py`** — Read-only Neo4j repository executing Cypher queries using official `neo4j` Python driver.
- ✅ **`api/schemas/chat.py`** — Pydantic request (`ChatRequest`) and response (`ChatResponse`) schemas.
- ✅ **`api/main.py`** — Registered `chat_router`.
- ✅ **`api/requirements.txt`** — Added `neo4j==5.19.0`.

---

## Supported Questions & Cypher Mappings

| Question | Cypher Query |
|----------|--------------|
| **How many customers are there?** | `MATCH (c:Customer) RETURN count(c) AS count` |
| **List all customers** | `MATCH (c:Customer) RETURN c.customerId AS customerId, c.name AS name, c.city AS city ORDER BY toInteger(c.customerId)` |
| **Show customer 1** | `MATCH (c:Customer {customerId: $customerId}) RETURN c` |
| **Show customers from Chennai** | `MATCH (c:Customer) WHERE toLower(c.city) = $city RETURN c` |
| **Show customers from Coimbatore** | `MATCH (c:Customer) WHERE toLower(c.city) = $city RETURN c` |
| **Show all emails** | `MATCH (c:Customer) RETURN c.email AS email` |
| **Show all cities** | `MATCH (c:Customer) RETURN DISTINCT c.city AS city` |

---

## Fallback Behavior

Unsupported questions return:
```json
{
  "answer": "Sorry, I can answer only questions about the graph database."
}
```

---

## Logging Metrics

Every request logs:
- `Question received`
- `Cypher generated`
- `Execution time` (ms)
- `Number of records returned`
