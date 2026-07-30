# Viva Q&A – Milestone 06: Graph Query API and Chat Backend

## Q1. Why use predefined Cypher query mapping instead of an LLM or RAG?
**Answer:** Predefined query mapping guarantees 100% determinism, zero hallucinations, zero external API costs, instant millisecond execution time, and strict data security compliance for hackathon and enterprise backends.

## Q2. How is clean architecture enforced in the Chat Backend?
**Answer:**
- Controller (`controller.py`) handles only HTTP parsing and response status mapping.
- Service (`service.py`) handles execution timing, metrics logging, and result formatting.
- Mapper (`query_mapper.py`) holds all Cypher queries separately.
- Repository (`repository.py`) executes Neo4j driver read sessions.

## Q3. How does the system handle unsupported questions?
**Answer:** The `QueryMapper` returns `None` for unsupported questions, triggering `ChatService` to return `{"answer": "Sorry, I can answer only questions about the graph database."}` without querying Neo4j or failing.

## Q4. How are execution timing and record metrics captured?
**Answer:** `ChatService` captures high-precision timestamp using `time.perf_counter()` before and after repository execution, logging execution time in milliseconds along with record count.
