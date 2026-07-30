# GraphChatEngine – Presentation & Pitch Notes

---

## 1. 2-Minute Elevator Pitch

> "Hello judges! We built **GraphChatEngine** — an end-to-end, containerized real-time data pipeline and knowledge-graph chatbot.
>
> Relational databases and raw CSV files are hard to query intuitively and struggle with complex relationship traversals. GraphChatEngine bridges this gap:
>
> 1. A user uploads a CSV file to our FastAPI endpoint.
> 2. The API validates the file and instantly streams each row to Apache Kafka.
> 3. An isolated worker service consumes from Kafka and inserts nodes directly into Neo4j using idempotent Cypher `MERGE` statements.
> 4. Finally, users can ask natural language questions through our ChatGPT-style frontend interface, which queries Neo4j in sub-50 milliseconds with zero hallucinations and zero external AI API costs.
>
> The entire stack runs seamlessly in Docker with a single `docker compose up --build` command!"

---

## 2. 5-Minute Presentation Outline

### Minute 1: Problem & Solution
- **The Problem:** Tabular CSV data is static, trapped in silos, and difficult for business users to query without knowing SQL or graph languages.
- **The Solution:** GraphChatEngine turns tabular data into an event-streamed, graph-backed conversational experience.

### Minute 2: System Architecture
- Explain the 5-stage pipeline: `CSV` -> `FastAPI` -> `Kafka Producer` -> `Kafka Consumer (Loader)` -> `Neo4j` -> `Chat Backend` -> `Frontend UI`.
- Highlight **Clean Architecture**: Routers handle HTTP; Services handle domain logic; Repositories handle database drivers.

### Minute 3: Key Technical Highlights
- **Apache Kafka in KRaft Mode:** No ZooKeeper required. Producer uses `acks='all'` and partition keying for ordered, durable streaming.
- **Idempotent Neo4j Writes:** Cypher `MERGE` prevents duplicate nodes even during network retries or re-uploads.
- **Deterministic Chat Engine:** Answers queries in under 50ms without external LLM API costs or AI hallucinations.

### Minute 4: Live Demonstration
- Upload `customers.csv` (20 rows) via `POST /ingest`.
- Show Kafka & Loader logs streaming messages live.
- Execute Cypher query in Neo4j Browser showing `20` Customer nodes.
- Open Frontend UI and ask *"How many customers are there?"* and *"Show customer 1"*.

### Minute 5: Summary & Q&A
- Recap hackathon milestones completed (1 through 8).
- Open floor for judge Q&A.

---

## 3. 10-Minute Deep Dive Presentation Outline

- **0:00 - 1:30:** Introduction & Hackathon Challenge Overview.
- **1:30 - 3:30:** Microservices Architecture & Docker Containerization Strategy.
- **3:30 - 5:30:** Event Streaming with Kafka (KRaft mode, producer acks, consumer offset management).
- **5:30 - 7:00:** Neo4j Knowledge Graph Design & Cypher `MERGE` Idempotency.
- **7:00 - 8:30:** Live End-to-End Demo (CSV Upload -> Stream -> Graph -> Chat UI).
- **8:30 - 10:00:** Technical Q&A & Architecture Defense.

---

## 4. Demo Flow Checklist

1. **Docker Compose:** Run `docker ps` to display 4 healthy containers.
2. **Swagger UI:** Open `http://localhost:8000/docs` to demonstrate OpenAPI endpoints.
3. **Upload CSV:** Send `customers.csv` via `POST /ingest`.
4. **Inspect Kafka & Loader Logs:** Show real-time container log output.
5. **Neo4j Browser:** Run `MATCH (c:Customer) RETURN count(c)` -> displays `20`.
6. **Frontend Chat UI:** Ask preset questions and view instant responses.
