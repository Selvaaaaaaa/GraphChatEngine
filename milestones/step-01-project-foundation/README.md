# GraphChatEngine

> **CSV → Kafka → Neo4j Chatbot** — A real-time data pipeline and knowledge-graph chatbot built for hackathon development.

---

## Overview

GraphChatEngine is a production-style, containerised pipeline that:

1. **Ingests** CSV files through a REST API
2. **Streams** records through Apache Kafka
3. **Stores** entities and relationships in a Neo4j graph database
4. **Answers** natural-language questions about the data via a chatbot UI

The project is developed **incrementally across milestones**, starting with a clean infrastructure skeleton and progressively adding business logic.

---

## Folder Structure

```
csv-graph-chatbot/
├── api/
│   ├── main.py            # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile
├── loader/
│   ├── loader.py          # Worker service (Kafka consumer → Neo4j writer)
│   ├── requirements.txt
│   └── Dockerfile
├── ui/
│   ├── index.html         # Single-page UI
│   ├── style.css
│   └── app.js
├── milestones/            # Snapshots of each milestone
├── docker-compose.yml
├── .env.example           # Copy to .env and fill in credentials
├── .gitignore
└── README.md
```

---

## Services

| Service  | Image / Build                | Port(s)       | Purpose                                      |
|----------|------------------------------|---------------|----------------------------------------------|
| `kafka`  | `apache/kafka:3.7.0`         | `9092`        | Message broker (KRaft, no ZooKeeper)         |
| `neo4j`  | `neo4j:5.19-community`       | `7474`, `7687`| Graph database (Browser + Bolt)              |
| `api`    | Built from `./api/Dockerfile`| `8000`        | FastAPI backend — CSV upload, chat endpoints |
| `loader` | Built from `./loader/Dockerfile` | —         | Internal worker — reads Kafka, writes Neo4j  |

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24.x  
- [Docker Compose](https://docs.docker.com/compose/) ≥ 2.x (bundled with Docker Desktop)

### 1 — Clone the repository

```bash
git clone https://github.com/Selvaaaaaaa/GraphChatEngine.git
cd GraphChatEngine
```

### 2 — Configure environment variables

```bash
cp .env.example .env
# Edit .env and set a strong NEO4J_PASSWORD
```

### 3 — Start all services

```bash
docker compose up --build
```

The first run downloads images and builds containers (~2–3 min).

### 4 — Verify services

| Service         | URL                              |
|-----------------|----------------------------------|
| API root        | http://localhost:8000/           |
| API health      | http://localhost:8000/health     |
| API docs        | http://localhost:8000/docs       |
| Neo4j Browser   | http://localhost:7474            |
| UI              | Open `ui/index.html` in browser  |

### Stopping

```bash
docker compose down          # Stop and remove containers
docker compose down -v       # Also remove named volumes (data loss!)
```

---

## Milestones

| #  | Name                  | Status      |
|----|-----------------------|-------------|
| 01 | Project Foundation    | ✅ Complete |
| 02 | Kafka Producer        | 🔜 Planned  |
| 03 | Neo4j Integration     | 🔜 Planned  |
| 04 | Chatbot / NLP         | 🔜 Planned  |

---

## Development Notes

- All services share the `graphchat-net` Docker bridge network.
- Named Docker volumes (`kafka-data`, `neo4j-data`, `neo4j-logs`) persist data across restarts.
- Health checks are configured so dependent services wait until Kafka and Neo4j are ready.
- The loader service uses `restart: unless-stopped` so it recovers from transient failures.

---

## License

MIT
