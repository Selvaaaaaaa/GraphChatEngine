# GraphChatEngine – Required Screenshots Manifest

> List of all required screenshots for final report, GitHub repository, presentation slides, and hackathon judge evaluation.

---

## Required Screenshots List

| # | Screenshot Identifier | Description / View | Location / URL |
|---|----------------------|--------------------|----------------|
| **1** | `01_docker_containers_running.png` | Terminal view of `docker ps` showing 4 healthy running containers (`graphchat-api`, `graphchat-loader`, `graphchat-kafka`, `graphchat-neo4j`) | Terminal CLI |
| **2** | `02_swagger_api_docs.png` | OpenAPI / Swagger UI interface showing `POST /ingest`, `POST /chat`, and `GET /health` | `http://localhost:8000/docs` |
| **3** | `03_csv_upload_response.png` | `POST /ingest` execution uploading `customers.csv` and returning HTTP 200 `status: "published"` | Swagger / Postman / Terminal |
| **4** | `04_kafka_producer_logs.png` | API container logs displaying `Kafka connected`, `Publishing started`, and `messages_published=20` | `docker compose logs api` |
| **5** | `05_kafka_consumer_logs.png` | Loader worker logs displaying `Received Message`, `Creating Customer Node`, and `Customer Inserted` | `docker compose logs loader` |
| **6** | `06_neo4j_browser_node_count.png` | Neo4j Browser executing `MATCH (c:Customer) RETURN count(c)` returning count `20` | `http://localhost:7474` |
| **7** | `07_neo4j_browser_graph_visual.png` | Neo4j Browser visual graph bubbles executing `MATCH (c:Customer) RETURN c LIMIT 5` | `http://localhost:7474` |
| **8** | `08_frontend_welcome_screen.png` | Frontend Chat UI on initial load showing sidebar, pipeline architecture, preset chips, and bot welcome card | `ui/index.html` |
| **9** | `09_frontend_conversation.png` | Frontend Chat UI showing active conversation with user bubbles and bot answer bubbles | `ui/index.html` |
| **10** | `10_browser_console_metrics.png` | Browser Developer Console displaying logged `Question`, `API Response`, and `Execution time` | F12 DevTools Console |
