# GraphChatEngine – Final Viva & Technical Q&A Guide

> 50 Comprehensive Interview Questions & Detailed Technical Answers covering the full stack: FastAPI, Docker, Kafka, Neo4j, Cypher, Frontend, System Design, Error Handling, and Architecture.

---

## Part 1: FastAPI & REST API (Q1 - Q8)

### Q1. What is FastAPI and why was it chosen for the API backend?
**Answer:** FastAPI is a high-performance Python web framework based on ASGI standards (Starlette and Pydantic). It was chosen for its automatic OpenAPI/Swagger documentation generation, native asynchronous support (`async`/`await`), strict type hints, and low latency.

### Q2. How does `UploadFile` work in FastAPI for CSV ingestion?
**Answer:** `UploadFile` uses a Python spool file stream stored in memory up to a threshold before writing to disk. It exposes asynchronous `.read()` methods to stream raw byte arrays into `pandas.read_csv(io.BytesIO(raw_bytes))` without saving temporary files to disk.

### Q3. What is the role of Pydantic schemas in this project?
**Answer:** Pydantic schemas (`IngestPublishedResponse`, `ChatRequest`, `ChatResponse`) enforce data validation, serialize Python objects into JSON payloads, and drive auto-generated OpenAPI schemas in Swagger UI.

### Q4. How does FastAPI handle CORS (Cross-Origin Resource Sharing)?
**Answer:** FastAPI uses `CORSMiddleware` to attach response headers (`Access-Control-Allow-Origin: *`) allowing browser clients on different ports/domains (e.g. frontend on port 3000) to execute cross-origin requests.

### Q5. What is ASGI vs WSGI?
**Answer:** WSGI (Web Server Gateway Interface) is synchronous and handles one request per thread. ASGI (Asynchronous Server Gateway Interface) supports async event loops, enabling high concurrency for long-lived I/O operations like streaming or WebSockets.

### Q6. How are HTTP errors handled in `POST /ingest`?
**Answer:** Custom exceptions like `CSVValidationError` map business failures (wrong extension, empty file, malformed rows) to explicit HTTP status codes (HTTP 400 Bad Request, HTTP 422 Unprocessable Entity) with structured JSON error bodies.

### Q7. Why does FastAPI use background startup events (`@app.on_event("startup")`)?
**Answer:** Startup handlers configure global logging configurations, verify dependency settings, and log startup diagnostic banners before Uvicorn starts accepting incoming HTTP traffic.

### Q8. What is the difference between path parameters and query parameters in FastAPI?
**Answer:** Path parameters are part of the URL path (`/jobs/{job_id}`). Query parameters follow a question mark in the URL (`/jobs?status=completed`). `POST` request bodies carry JSON payloads in the request HTTP body.

---

## Part 2: Docker & Infrastructure (Q9 - Q15)

### Q9. What containers compose the GraphChatEngine stack?
**Answer:**
1. `graphchat-api` (FastAPI web engine)
2. `graphchat-loader` (Python Kafka consumer & Neo4j loader worker)
3. `graphchat-kafka` (Apache Kafka broker in KRaft mode)
4. `graphchat-neo4j` (Neo4j Community graph database)

### Q10. What is Apache Kafka KRaft mode?
**Answer:** KRaft (Kafka Raft Metadata mode) allows Kafka to manage its own consensus metadata without requiring an external Apache ZooKeeper ensemble, reducing operational complexity and container resource usage.

### Q11. Why use Python `urllib` in the API Docker health check instead of `curl` or `wget`?
**Answer:** `python:3.11-slim` images strip non-essential OS binaries like `curl` and `wget`. Running `python -c "import urllib.request; urllib.request.urlopen(...)"` uses standard library Python, eliminating external binary dependencies.

### Q12. What is the purpose of Docker networks (`graphchat-net`)?
**Answer:** Docker bridge networks provide isolated container-to-container communication using internal container names (e.g. `kafka:29092`, `neo4j:7687`) as DNS hostnames, isolated from external host traffic.

### Q13. How does `depends_on: condition: service_healthy` work in Docker Compose?
**Answer:** It ensures dependent containers (like `api` or `loader`) wait to start until upstream infrastructure dependencies (like `kafka` and `neo4j`) have fully booted and passed their health check probes.

### Q14. What is multi-stage Docker layer caching?
**Answer:** Copying `requirements.txt` and running `pip install` before copying application source code ensures Docker reuses cached dependency layers on rebuilds unless `requirements.txt` changes.

### Q15. How are secrets managed in Docker Compose?
**Answer:** Environment variables are loaded from `.env` files via `.env.example` templates, keeping sensitive secrets out of committed source code.

---

## Part 3: Kafka Producer & Event Streaming (Q16 - Q23)

### Q16. What is `kafka-python` and how is it configured?
**Answer:** `kafka-python` is the native client library. `KafkaProducer` is configured with `bootstrap_servers='kafka:29092'`, `value_serializer` (dict to UTF-8 JSON bytes), and `key_serializer` (string to UTF-8 bytes).

### Q17. What does `acks='all'` guarantee in the producer?
**Answer:** `acks='all'` forces the producer to wait for all in-sync broker replicas to acknowledge receipt of the message before considering the write successful, preventing message loss.

### Q18. Why use `job_id` as the Kafka message key?
**Answer:** Kafka hashes message keys to assign partition numbers. Using `job_id` as key ensures all CSV rows belonging to the same upload job land in the same partition, guaranteeing ordered consumption.

### Q19. Why is `producer.flush()` called after the publish loop?
**Answer:** `producer.send()` is asynchronous and buffers messages in memory. `flush()` blocks execution until all buffered records are transmitted to the broker and acknowledged.

### Q20. How is `NaN` handled during JSON serialization?
**Answer:** pandas missing values (`float('nan')`) are converted to Python `None` via `dataframe.where(pd.notnull(df), None)` before `json.dumps()`, outputting valid JSON `null` values.

### Q21. What happens if Kafka is unavailable when the API tries to produce messages?
**Answer:** `NoBrokersAvailable` is caught in `_build_producer()` and converted to `KafkaPublishError` with status code 503 (Service Unavailable), returning a descriptive JSON error to the caller.

### Q22. What is message partition ordering in Kafka?
**Answer:** Kafka guarantees strict message ordering **only within a single partition**. By partitioning messages with `job_id`, row order within a job is preserved.

### Q23. What is `max_block_ms` in KafkaProducer?
**Answer:** `max_block_ms=10000` bounds the maximum time `send()` will block when the internal buffer is full before raising an exception, preventing infinite HTTP hangs.

---

## Part 4: Kafka Consumer & Loader Worker (Q24 - Q31)

### Q24. What is a Consumer Group?
**Answer:** A Consumer Group is a group of consumers sharing the load of reading from a topic. Kafka assigns topic partitions among group members and tracks offsets per group.

### Q25. What is `AUTO_OFFSET_RESET='earliest'`?
**Answer:** It instructs the consumer to read messages from the beginning of the topic log whenever no previous committed offset exists for the consumer group.

### Q26. How does the consumer handle malformed JSON messages?
**Answer:** `_deserialize_value` wraps `json.loads` in a `try...except (json.JSONDecodeError, UnicodeDecodeError)` block, returning `None` and logging a warning without stopping the consumer poll loop.

### Q27. What fields are required during message schema validation?
**Answer:** `job_id`, `row_number`, `timestamp`, and `data`. Missing fields trigger rejection and skip the record.

### Q28. How does `consumer.poll(timeout_ms=1000)` operate?
**Answer:** `poll()` issues a pull request to the broker for available record batches, blocking up to 1000ms while maintaining background consumer heartbeats.

### Q29. How is graceful container shutdown implemented in `consumer.py`?
**Answer:** Signal handlers intercept `SIGINT`/`SIGTERM`, set `running=False`, and invoke `consumer.close(timeout=5)`, releasing consumer group partitions cleanly.

### Q30. Why is the consumer isolated in a separate worker container (`loader`)?
**Answer:** Decoupling ingestion (API) from processing (Loader) allows the API to respond immediately while the Loader processes heavy database writes asynchronously without blocking HTTP threads.

### Q31. What is the role of `memory_store` in Milestone 04?
**Answer:** It temporarily buffers validated message objects in worker memory before database insertion logic was connected in Milestone 05.

---

## Part 5: Neo4j & Cypher Graph Database (Q32 - Q40)

### Q32. What is Neo4j?
**Answer:** Neo4j is a native graph database management system that stores data as nodes, labels, properties, and directed relationships with index-free adjacency.

### Q33. Why use `MERGE` instead of `CREATE` in Cypher?
**Answer:** `MERGE` matches existing nodes by primary property (`customerId`) or creates them if missing, ensuring idempotent upserts without creating duplicate graph nodes.

### Q34. What is a Cypher Label?
**Answer:** A Label (e.g. `:Customer`) categorizes nodes into collections, enabling schema indexing and targeted pattern matching.

### Q35. What is a Cypher Property?
**Answer:** A Property is a key-value pair stored on a node or relationship (e.g. `c.name = $Name`).

### Q36. What is the Bolt protocol?
**Answer:** Bolt (`bolt://`) is Neo4j's binary database connection protocol operating on port 7687, offering optimized binary serialization and connection pooling over HTTP REST.

### Q37. How does parameter binding (`$CustomerID`) prevent Cypher Injection?
**Answer:** Parameterization separates query code from user data, preventing arbitrary Cypher code injection and allowing query plan caching.

### Q38. How does `Neo4jRepository` handle field key normalization?
**Answer:** It checks multiple key variations (`CustomerID`, `customerId`, `id`) defensively, ensuring Cypher parameters receive clean values regardless of CSV header formatting.

### Q39. What is Index-Free Adjacency?
**Answer:** Nodes maintain direct physical disk/memory pointers to connected neighbor nodes, enabling $O(1)$ relationship traversal independent of total database size.

### Q40. How do you query node count in Neo4j?
**Answer:** `MATCH (c:Customer) RETURN count(c) AS count`.

---

## Part 6: Frontend & System Architecture (Q41 - Q50)

### Q41. How does the Frontend communicate with the Chat API?
**Answer:** `app.js` issues asynchronous `fetch()` requests (`POST http://localhost:8000/chat`) with JSON body `{"question": "..."}`.

### Q42. Why use predefined Cypher mapping instead of LLMs or RAG for Milestone 06?
**Answer:** Predefined mapping guarantees 100% deterministic answers, zero AI hallucinations, sub-50ms query execution, and zero external API costs.

### Q43. How does the UI handle typing indicator animations?
**Answer:** `showTypingIndicator()` appends a temporary bot bubble with animated bouncing dots (`.typing-dot`), which is removed when the response arrives.

### Q44. How does `performance.now()` measure query execution time?
**Answer:** Timestamps are recorded before and after `fetch()`, yielding high-precision millisecond timing printed to the browser console.

### Q45. How does the UI handle backend disconnects?
**Answer:** Network errors trigger `catch` blocks rendering red error message bubbles (`⚠️ Unable to connect to GraphChatEngine backend`).

### Q46. How are unsupported chat questions handled?
**Answer:** `QueryMapper` returns `None`, prompting the service to respond: `"Sorry, I can answer only questions about the graph database."`

### Q47. What is clean architecture in the Chat module?
**Answer:** Controller handles HTTP parsing -> Service handles timing & metrics -> Mapper handles Cypher definitions -> Repository handles Neo4j Bolt driver queries.

### Q48. What is the purpose of the health check probe (`GET /health`)?
**Answer:** It provides a zero-overhead probe endpoint for load balancers, Docker health checks, and frontend status indicators.

### Q49. How does the UI support mobile responsiveness?
**Answer:** CSS media queries (`@media (max-width: 768px)`) hide the left sidebar and adapt message bubbles to fit mobile viewports cleanly.

### Q50. How is the system packaged for hackathon delivery?
**Answer:** The entire pipeline is fully containerized via `docker-compose.yml`, startable with `docker compose up --build`, and snapshot-preserved across milestone directories.
