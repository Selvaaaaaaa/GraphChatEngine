# Architecture – Milestone 06: Graph Query API and Chat Backend

```
Client (HTTP POST /chat)
         │
         ▼
  [controller.py]  (FastAPI Router)
         │
         ▼
    [service.py]   (Chat Service & Timing / Metrics Logger)
       ┌─┴────────────────────────┐
       ▼                          ▼
[query_mapper.py]         [repository.py]
(Predefined Cypher)       (Neo4j Driver Read Query)
                                  │
                                  ▼
                          ┌──────────────┐
                          │    Neo4j     │
                          │  Database    │
                          └──────────────┘
```

## Clean Architecture Layers

1. **Controller Layer (`api/chat/controller.py`)**:
   - Parses HTTP `ChatRequest` (`question: str`).
   - Delegates business logic to `ChatService`.
   - Handles `Neo4jChatRepositoryError` -> HTTP 503 / 500 status codes.
   - Strictly contains zero Cypher query strings.

2. **Service Layer (`api/chat/service.py`)**:
   - Orchestrates question matching via `QueryMapper`.
   - Executes Cypher query using `Neo4jChatRepository`.
   - Logs performance metrics: question received, generated Cypher, execution time (ms), and record count.
   - Formats Cypher record outputs into human-readable answer strings.

3. **Query Mapper Layer (`api/chat/query_mapper.py`)**:
   - Stores all predefined Cypher query templates and parameter extractors separately.
   - Formats result lists into string answers.
   - Handles unsupported questions with fallback answer.

4. **Repository Layer (`api/chat/repository.py`)**:
   - Manages read sessions against Neo4j Graph Database using official `neo4j` Python driver.
