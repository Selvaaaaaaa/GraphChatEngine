# Next Step – Milestone 05: Neo4j Integration & Graph Insertion

## What Milestone 05 Will Implement

Milestone 05 connects the Loader's Kafka consumer to Neo4j, converting streamed CSV row dictionaries into graph nodes and relationships.

### Features

1. **Neo4j Driver Integration in `loader/`**
   - Add `neo4j==5.19.0` to `loader/requirements.txt`.
   - Create `loader/services/neo4j_service.py` to manage Bolt driver connections and session transactions.

2. **Cypher Statement Generator (`loader/services/cypher_builder.py`)**
   - Translate dictionary records into Cypher `MERGE` queries.
   - Map entity types:
     - `:Customer` nodes with `LOCATED_IN` edges to `:City` / `:Country`.
     - `:Employee` nodes with `REPORTS_TO` hierarchical edges.
     - `:Product` and `:Order` nodes with purchase edges.

3. **Database Write Execution**
   - Execute Cypher transactions inside `IngestConsumerService.process_message()`.
   - Commit offsets only after successful Neo4j insertion.

4. **Verification**
   - Verify nodes and relationships in Neo4j Browser (`http://localhost:7474`).
