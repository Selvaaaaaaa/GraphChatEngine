# Next Step – Milestone 06: Chatbot & Natural Language Graph Queries

## What Milestone 06 Will Implement

Milestone 06 builds the natural-language Chatbot interface on top of the populated Neo4j Knowledge Graph.

### Features

1. **Natural Language to Cypher Translator (`api/services/chatbot_service.py`)**
   - Translate user questions (e.g. *"Who are the customers from the USA?"*) into valid Cypher queries (`MATCH (c:Customer {country: "USA"}) RETURN c.name`).
   - Execute queries against Neo4j and format human-readable answers.

2. **Chatbot API Endpoint (`POST /chat`)**
   - `POST /chat` endpoint accepting user messages `{ "question": "..." }`.
   - Returns answer payload `{ "answer": "...", "cypher_query": "..." }`.

3. **UI Integration (`ui/app.js` & `ui/index.html`)**
   - Connect the web UI chat input to `POST /chat`.
   - Display dynamic chat conversation history and generated Cypher queries.
