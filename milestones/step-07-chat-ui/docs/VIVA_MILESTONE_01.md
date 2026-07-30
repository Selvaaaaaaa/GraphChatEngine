# VIVA NOTES – Milestone 01 & 01.5: Project Foundation & Hardening

> 20 professional viva questions with detailed, accurate answers.
> Covers Docker, Docker Compose, FastAPI, Neo4j, Kafka, Health Checks, REST API, Environment Variables, and Container Networking.

---

## Q1. What is Docker Compose and why is it used in this project?

**Answer:**
Docker Compose is a tool for defining and running multi-container Docker applications using a single YAML file (`docker-compose.yml`). Instead of running four separate `docker run` commands with dozens of flags, a single `docker compose up` starts all services with the correct configuration, networking, and dependencies.

In this project it manages four services: Kafka, Neo4j, the FastAPI API, and the Loader worker — all on a shared network, with health checks, named volumes, and environment variable injection.

---

## Q2. What is the difference between `CMD` and `ENTRYPOINT` in a Dockerfile?

**Answer:**
- `CMD` provides **default arguments** that can be overridden at `docker run`. If a command is passed to `docker run`, CMD is replaced entirely.
- `ENTRYPOINT` sets the **fixed executable**. Arguments from CMD (or `docker run`) are appended to it.

In this project, we use `CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]` because we want the command to be fully replaceable during development (e.g., to run a shell for debugging), while keeping the default behaviour clean.

---

## Q3. Why does the API health check use Python's `urllib` instead of `wget` or `curl`?

**Answer:**
The base image `python:3.11-slim` is intentionally minimal — it includes Python and pip, but **not** `wget` or `curl`. Running `wget` in the health check would silently fail with exit code 1 because the binary doesn't exist, causing the container to always report `unhealthy`.

The solution is to use `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"`. Python is guaranteed to be present in the image, `urllib` is part of the standard library (no install needed), and the call raises an exception (causing a non-zero exit code) on failure. This is a zero-dependency, portable health check.

---

## Q4. What is Kafka KRaft mode and why is it used instead of ZooKeeper?

**Answer:**
KRaft (Kafka Raft) is Kafka's built-in metadata management protocol, replacing the previously mandatory Apache ZooKeeper dependency. Introduced in Kafka 2.8 and production-stable since 3.3+.

**Why KRaft:**
- **Simpler architecture** — one fewer service to manage, configure, and monitor
- **Faster failover** — KRaft controller elections are significantly faster
- **Reduced resource use** — no separate ZooKeeper JVM process
- **Unified configuration** — all Kafka settings in one place

In this project, setting `KAFKA_PROCESS_ROLES: broker,controller` runs both roles in a single container (combined mode), ideal for development.

---

## Q5. What is `depends_on: condition: service_healthy` in Docker Compose?

**Answer:**
It is a startup ordering directive that tells Docker Compose to wait until a dependency passes its health check before starting the dependent service.

```yaml
api:
  depends_on:
    kafka:
      condition: service_healthy
    neo4j:
      condition: service_healthy
```

Without this, Docker starts all containers in parallel. The API might try to connect to Kafka before Kafka finishes its 30-second initialisation, causing `ConnectionRefusedError` crashes. `service_healthy` solves this elegantly — Docker polls the health check and only starts the API once both dependencies are `healthy`.

---

## Q6. What is the purpose of `PYTHONPATH=/app` in the API Dockerfile?

**Answer:**
The API source is copied into `/app/api/` inside the container (not directly into `/app`). For Python's import system to resolve `from api.services.ingest_service import ...`, it needs to find the `api` package.

Setting `ENV PYTHONPATH=/app` tells Python to add `/app` to `sys.path`. Python then finds `/app/api/` as the `api` package, and all submodule imports work correctly. Without this, every import would raise `ModuleNotFoundError: No module named 'api'`.

---

## Q7. What is FastAPI and what advantages does it offer?

**Answer:**
FastAPI is a modern Python web framework built on ASGI (Asynchronous Server Gateway Interface). Key advantages:

| Feature              | Benefit                                                  |
|----------------------|----------------------------------------------------------|
| **Pydantic schemas** | Automatic request validation and response serialization  |
| **OpenAPI/Swagger**  | Auto-generated interactive documentation at `/docs`      |
| **Async support**    | Non-blocking I/O — handles concurrent requests efficiently|
| **Type hints**       | Editor autocomplete, static analysis, self-documentation |
| **Performance**      | One of the fastest Python frameworks (on par with Node.js)|

In this project, Pydantic schemas (`IngestSuccessResponse`, `ErrorResponse`) serve dual purposes: they validate data and automatically populate the Swagger UI with examples.

---

## Q8. What is the Bolt protocol in Neo4j?

**Answer:**
Bolt is Neo4j's binary client-server protocol for driver connections. Characteristics:
- **Binary format** — more efficient than HTTP for query execution
- **Persistent connections** — supports connection pooling
- **Port 7687** — the standard Bolt port
- **Used by** — all official Neo4j drivers (Python, Java, JavaScript, Go)

In contrast, port 7474 serves the HTTP API and the Neo4j Browser UI (a web interface). Drivers should always connect via Bolt (`bolt://neo4j:7687`) for best performance.

---

## Q9. Explain the two Kafka listeners and why they are different.

**Answer:**

```yaml
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:29092, PLAINTEXT_HOST://0.0.0.0:9092
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092, PLAINTEXT_HOST://localhost:9092
```

Two listeners are needed because Kafka advertises its address to clients, and the correct address differs based on where the client is:

| Listener         | Port  | Used by                              | Hostname advertised |
|------------------|-------|--------------------------------------|---------------------|
| `PLAINTEXT`      | 29092 | Containers inside Docker network     | `kafka:29092`       |
| `PLAINTEXT_HOST` | 9092  | Applications on the host machine     | `localhost:9092`    |

If only one listener were configured, either Docker-internal services or host-machine clients would fail to connect — they use different DNS names for the same broker.

---

## Q10. What is a named Docker volume and why is it important?

**Answer:**
A named volume (`kafka-data`, `neo4j-data`) is a Docker-managed persistent storage location outside the container's filesystem. It survives `docker compose down` (container removal) but is deleted only with `docker compose down -v`.

**Without named volumes:** All Kafka messages and Neo4j graph data would be lost every time containers are removed. This means data would have to be re-ingested every session.

**With named volumes:** Data persists across restarts, just like a normal database on a server.

---

## Q11. What is `multipart/form-data` and why is it used for CSV uploads?

**Answer:**
`multipart/form-data` is an HTTP encoding scheme defined in RFC 7578 for sending mixed payloads (files + form fields) in a single HTTP request. It splits the body into parts, each with its own Content-Type and Content-Disposition header.

**Why not JSON?** `application/json` is text-only. While binary data can be Base64-encoded in JSON, it increases payload size by ~33% and requires encoding/decoding on both ends. `multipart/form-data` sends raw binary efficiently.

**Why not `application/octet-stream`?** This works for single file uploads but cannot mix files with metadata fields. `multipart/form-data` is the standard for HTML `<form>` file uploads and is supported natively by browsers, curl, and every HTTP client library.

---

## Q12. What does `restart: unless-stopped` mean in Docker Compose?

**Answer:**
It tells Docker to automatically restart a container if it exits, unless it was explicitly stopped by the user.

| Restart Policy      | Behaviour                                                   |
|---------------------|-------------------------------------------------------------|
| `no` (default)      | Never restart automatically                                 |
| `always`            | Restart always, including after system reboots              |
| `on-failure`        | Restart only on non-zero exit codes                         |
| `unless-stopped`    | Restart always, **except** when manually stopped with `docker stop` |

`unless-stopped` is the best choice for development — it handles transient failures (network blips, OOM events) automatically, but doesn't restart containers that were intentionally stopped.

---

## Q13. How does Docker's internal DNS work within a bridge network?

**Answer:**
When containers share a Docker bridge network (like `graphchat-net`), Docker's embedded DNS server automatically resolves **service names** to container IP addresses.

For example, when the API container runs `urllib.request.urlopen('http://localhost:8000/health')`, it uses its own loopback. But when it needs to connect to Kafka in Milestone 03, it will use `kafka:29092` — Docker resolves `kafka` to the actual IP of the `graphchat-kafka` container. No manual IP management or hosts file editing is required.

This is why environment variables use service names: `NEO4J_URI=bolt://neo4j:7687`, `KAFKA_BOOTSTRAP_SERVERS=kafka:29092`.

---

## Q14. What is the purpose of `.env.example` vs `.env`?

**Answer:**

| File          | Committed to Git | Contains real secrets | Purpose                           |
|---------------|------------------|-----------------------|-----------------------------------|
| `.env.example`| ✅ Yes           | ❌ No (placeholders)  | Documents required variables for new developers |
| `.env`        | ❌ No (.gitignore)| ✅ Yes               | Actual runtime configuration      |

`.env.example` follows the **12-Factor App** methodology for configuration. Developers clone the repo, copy `.env.example` to `.env`, fill in real values, and the application reads from `.env`. This pattern prevents accidental secret exposure while ensuring all developers know which variables to configure.

---

## Q15. What is Pydantic and how does it help in FastAPI?

**Answer:**
Pydantic is a Python library for data validation and serialization using type hints. In FastAPI:

1. **Request validation** — FastAPI automatically validates incoming request body against a Pydantic model. Invalid data returns HTTP 422 with descriptive errors, without any if/else code.
2. **Response serialization** — `response_model=IngestSuccessResponse` ensures the response is serialized correctly and extra fields are stripped.
3. **Swagger generation** — Pydantic's `Field(example=...)` and `model_config.json_schema_extra` populate the Swagger UI with realistic example values automatically.
4. **Type safety** — IDE autocomplete works correctly for model attributes.

---

## Q16. What is the difference between `HEALTHCHECK` in the Dockerfile vs `healthcheck:` in docker-compose.yml?

**Answer:**
Both define health check behaviour, but they operate at different levels:

| Location            | Scope                  | Override       |
|---------------------|------------------------|----------------|
| `Dockerfile HEALTHCHECK` | Baked into the image | docker-compose overrides it |
| `docker-compose.yml healthcheck:` | Applies at runtime | Takes precedence over Dockerfile |

In this project, the Dockerfile `HEALTHCHECK` is defined as a self-documenting default, while `docker-compose.yml` defines it explicitly (which takes precedence). Both use the same Python urllib command for consistency.

---

## Q17. Why is Neo4j a graph database better than a relational database for this use case?

**Answer:**
Relational databases (SQL) are optimised for aggregate queries over large tables. Graph databases are optimised for **traversal queries** — following relationships across multiple hops.

For the GraphChatEngine use case (finding connections between customers, orders, products, and locations), typical queries are:

```
"Find all products bought by customers who also bought product X"
"Who manages the manager of employee Y?"
"Which customers from the same country ordered the same product?"
```

These require expensive multi-table JOINs in SQL. In Neo4j, these are pattern matches on the graph — performance scales with the number of relevant nodes, not the total table size.

---

## Q18. What is ASGI and how does Uvicorn serve a FastAPI application?

**Answer:**
ASGI (Asynchronous Server Gateway Interface) is the Python standard for asynchronous web servers and applications, the async successor to WSGI.

**Request lifecycle:**
1. Client sends HTTP request to `localhost:8000`
2. **Uvicorn** (ASGI server) accepts the TCP connection and parses the HTTP protocol
3. Uvicorn calls the ASGI **FastAPI** application with a `scope`, `receive`, and `send` dictionary
4. FastAPI routes the request to the correct handler, runs dependency injection, validates input
5. Handler returns a response — FastAPI calls `send()` to stream it back through Uvicorn

The `--host 0.0.0.0` flag is critical inside Docker — without it, Uvicorn binds only to `127.0.0.1` (loopback), which is unreachable from outside the container.

---

## Q19. Explain the layered (clean architecture) structure of the API.

**Answer:**

```
routers/      ← HTTP layer: parse request, call service, return response
    ↓
services/     ← Business logic: validate, process, generate IDs
    ↓
utils/        ← Pure functions: no side effects, easy to unit-test
    ↓
schemas/      ← Data contracts: Pydantic models (shared by all layers)
    ↑
core/         ← Cross-cutting concerns: config, logging
```

**Benefits:**
- **Single responsibility** — each layer does one thing
- **Testability** — services and utils can be tested without an HTTP server
- **Extensibility** — adding Kafka in Milestone 03 requires only modifying `ingest_service.py`, not the router or schemas
- **Readability** — a new developer immediately knows where to look for HTTP logic vs business logic

---

## Q20. What happens when `docker compose down -v` is run, and when should it be used?

**Answer:**
`docker compose down -v` stops and removes all containers **and** deletes all named volumes.

**Effect on this project:**
- `kafka-data` → all Kafka topics and messages deleted
- `neo4j-data` → entire graph database deleted (all nodes, relationships, indexes)
- `neo4j-logs` → all Neo4j log files deleted

**When to use:**
- After major schema changes that require a clean database state
- When switching between incompatible versions of Kafka or Neo4j
- When troubleshooting data corruption issues

**When NOT to use:**
- During normal development — you would lose all test data
- In production — always use `docker compose down` (no `-v`) and back up volumes first
