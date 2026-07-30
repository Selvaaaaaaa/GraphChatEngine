# Milestone 01 – Project Foundation

## Objective

Establish a clean, production-style project skeleton for the **GraphChatEngine** (CSV → Kafka → Neo4j Chatbot). All four Docker services (`kafka`, `neo4j`, `api`, `loader`) start successfully via a single `docker compose up --build` command. No business logic (CSV parsing, Kafka messaging, Neo4j queries, or chatbot functionality) is implemented in this milestone.

---

## Features Completed

- ✅ **Docker Compose** configured with four services sharing a single bridge network
- ✅ **Apache Kafka 3.7** configured in KRaft mode (no ZooKeeper dependency)
- ✅ **Neo4j Community 5.19** configured with persistent volumes and auth via env vars
- ✅ **FastAPI service** (`api`) with `/` and `/health` endpoints, CORS enabled
- ✅ **Loader service** prints "Loader Started…" and keeps process alive
- ✅ **Basic UI** — dark-themed page displaying the pipeline and a live status indicator
- ✅ **Health checks** for all four services
- ✅ **Named volumes** for Kafka and Neo4j data persistence
- ✅ **`.env.example`** with all required environment variables
- ✅ **`.gitignore`** covering Python, Docker, IDE files, and secrets
- ✅ **README.md** with full setup instructions

---

## What Works

| Component                  | Status | Notes                                  |
|----------------------------|--------|----------------------------------------|
| `docker compose up --build`| ✅     | All four containers start and stay up  |
| `GET /`                    | ✅     | Returns `{"status":"running","service":"api"}` |
| `GET /health`              | ✅     | Returns `{"status":"ok"}`              |
| `GET /docs`                | ✅     | FastAPI auto-generated Swagger UI      |
| Neo4j Browser              | ✅     | Accessible at http://localhost:7474    |
| Kafka broker               | ✅     | Listening on port 9092 (KRaft mode)    |
| Loader process             | ✅     | Prints banner and runs indefinitely    |
| UI page                    | ✅     | Opens in browser; polls `/health`      |

---

## What Does NOT Work Yet

| Feature                             | Planned Milestone |
|-------------------------------------|-------------------|
| CSV file upload endpoint            | Milestone 02      |
| Kafka producer (API → Kafka)        | Milestone 02      |
| Kafka consumer (Loader reads Kafka) | Milestone 02      |
| Neo4j graph writes                  | Milestone 03      |
| Neo4j graph queries                 | Milestone 03      |
| Chatbot / NLP query interface       | Milestone 04      |
| UI upload form                      | Milestone 02      |
| UI chat panel                       | Milestone 04      |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Docker Network: graphchat-net       │
│                                                        │
│  ┌──────────┐   ┌──────────┐   ┌────────┐  ┌───────┐ │
│  │   API    │   │  Loader  │   │ Kafka  │  │ Neo4j │ │
│  │ :8000    │   │(worker)  │   │ :9092  │  │ :7687 │ │
│  │ FastAPI  │   │ Python   │   │ KRaft  │  │:7474  │ │
│  └──────────┘   └──────────┘   └────────┘  └───────┘ │
└──────────────────────────────────────────────────────┘
         ↑
    Host machine
    UI served from: ui/index.html
```

- **API** — stateless FastAPI service; will receive CSV uploads and serve chat responses
- **Loader** — long-running worker; will consume from Kafka and write to Neo4j
- **Kafka** — message broker decoupling the API from the Loader
- **Neo4j** — graph database storing entities and relationships extracted from CSV

---

## Commands

```bash
# Copy environment template
cp .env.example .env

# Build and start all services
docker compose up --build

# Start in background (detached)
docker compose up --build -d

# View logs for a specific service
docker compose logs -f api
docker compose logs -f loader

# Stop all containers
docker compose down

# Stop and remove volumes (clears all data)
docker compose down -v
```

---

## Viva Notes

**Q1. Why KRaft mode for Kafka?**  
KRaft (Kafka Raft) replaces ZooKeeper as the metadata store. Since Kafka 3.3+ it is production-stable, simplifies the deployment (one fewer service), and reduces operational overhead. This project uses it to keep the stack lean.

**Q2. What is the difference between `PLAINTEXT` and `PLAINTEXT_HOST` listeners?**  
`PLAINTEXT` (port 29092) is used for intra-container communication on the Docker network. `PLAINTEXT_HOST` (port 9092) is advertised to the host machine. Splitting listeners is required because internal and external addresses differ.

**Q3. Why does the API use `depends_on` with `condition: service_healthy`?**  
Without this, Docker starts containers in parallel and the API could crash trying to connect to Kafka or Neo4j before they are ready. Health-check conditions enforce a proper startup order.

**Q4. What does the Loader do in Milestone 01?**  
It prints a startup banner and enters a `while True: time.sleep(60)` loop. This keeps the container alive so Docker doesn't restart it, while providing a clean foundation to add Kafka consumer logic later.

**Q5. Why are named volumes used for Kafka and Neo4j?**  
Named volumes (`kafka-data`, `neo4j-data`) persist data between `docker compose down` and `docker compose up`. Without them, all data is lost every time containers are recreated.

**Q6. Why is CORS enabled on the API?**  
The UI is served as a static file from the host filesystem (or a future nginx container), so it has a different origin than the API. CORS middleware allows browsers to make cross-origin requests during development.

**Q7. What is the purpose of `.env.example`?**  
It documents all required environment variables without committing secrets. Developers copy it to `.env` (which is git-ignored) and fill in real values.

**Q8. Why does the Loader have an empty `requirements.txt`?**  
Only the Python standard library is needed in Milestone 01. The file is kept as a placeholder (with future packages commented out) so the Dockerfile layer-cache pattern works unchanged in later milestones.

**Q9. How does the UI know whether the API is running?**  
`app.js` polls `GET /health` every 5 seconds. If the response is `{"status":"ok"}`, the dot turns green and the message updates to "API Connected – System Ready".

**Q10. How is the Neo4j password configured?**  
Via the `NEO4J_AUTH` environment variable in the format `user/password`. The value is read from the `.env` file by Docker Compose using `${NEO4J_USER}/${NEO4J_PASSWORD}`.

---

## Report Notes

- The project uses a **microservices architecture** with four independently containerised services orchestrated by Docker Compose.
- **Apache Kafka 3.7 in KRaft mode** is chosen to eliminate ZooKeeper, reducing infrastructure complexity while maintaining production-grade message streaming capability.
- **Neo4j Community 5.19** provides a native graph storage model ideal for representing CSV data as entities and relationships, enabling graph-based queries that relational databases cannot efficiently support.
- All inter-service communication occurs over the **`graphchat-net` Docker bridge network**, isolating the stack from other containers on the host.
- **Persistent named volumes** (`kafka-data`, `neo4j-data`, `neo4j-logs`) ensure data survives container restarts and redeployments without requiring external storage.
- **Health checks** with `condition: service_healthy` in `depends_on` enforce correct startup ordering, preventing race conditions that would cause the API or Loader to crash on boot.
- The **FastAPI framework** was chosen for its automatic OpenAPI documentation (`/docs`), async support, and Pydantic-based validation — all essential for a fast-paced hackathon.
- **Environment variables** are externalised to `.env` (git-ignored), following the **12-Factor App** methodology for configuration management.
- The **UI** is built with plain HTML, CSS, and Vanilla JavaScript — no framework overhead — making it trivially deployable via any static file server or nginx container.
- The milestone-based development strategy creates **immutable snapshots** of each project state, enabling rollback, comparison, and clear demonstration of incremental progress.
