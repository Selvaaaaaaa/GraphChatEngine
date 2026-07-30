# VIVA NOTES – Milestone 05: Neo4j Graph Loader

> 20 professional viva questions with detailed answers.
> Covers Neo4j graph database fundamentals, Cypher query language, MERGE vs CREATE, Node/Label/Property concepts, driver architecture, and pipeline integration.

---

## Q1. Why use `MERGE` instead of `CREATE` in Cypher?

**Answer:**
- **`CREATE`** always creates a new node or relationship every time the statement is executed. If the same customer record is processed twice (e.g. re-uploading a CSV or re-consuming a message), `CREATE` will insert duplicate nodes into the graph database.
- **`MERGE`** acts as a "match or create" operation (upsert). It first searches the graph for a node matching the specified identifier (e.g. `{customerId: $CustomerID}`). If a matching node exists, it updates its properties using `SET`. If no match exists, it creates the node.

Using `MERGE` guarantees idempotency — re-processing the same CSV row multiple times will update the existing `:Customer` node rather than creating duplicate graph entities.

---

## Q2. Why use a Graph Database like Neo4j instead of a Relational (SQL) Database for this project?

**Answer:**
1. **Relationship-First Storage:** In SQL, relationships are virtualized using foreign key joins across separate tables, requiring costly `JOIN` operations that degrade performance exponentially as query depth (hops) increases. In Neo4j, relationships are stored as direct physical pointers on disk (index-free adjacency).
2. **Flexible Schema:** Graph databases support fluid schema evolution. Adding new entity types or relationships requires no complex schema migration scripts.
3. **Natural fit for Knowledge Graphs & Chatbots:** Answering natural-language questions like *"Which customers in Spain bought products manufactured by Supplier X?"* maps directly to graph pattern matching (`MATCH (c:Customer)-[:BOUGHT]->(p:Product)-[:SUPPLIED_BY]->(s:Supplier)`).

---

## Q3. What is a Node in Neo4j?

**Answer:**
A **Node** represents a discrete entity or record in the graph data model (equivalent to a row in a SQL table or an object instance in OOP).

In Milestone 05, each customer record from `customers.csv` becomes a distinct Node in Neo4j (e.g., node for Alice Johnson with `customerId: 1`).

---

## Q4. What is a Label in Neo4j?

**Answer:**
A **Label** is a tag or category applied to a Node to group similar entities together (equivalent to a table name in SQL). A node can have zero, one, or multiple labels.

In Milestone 05, customer nodes are tagged with the label `:Customer`. Labels allow efficient indexing and targeted querying (e.g., `MATCH (c:Customer)...`).

---

## Q5. What is a Property in Neo4j?

**Answer:**
A **Property** is a key-value pair stored on a Node or a Relationship (equivalent to a column value in SQL).

In Milestone 05, `:Customer` nodes store properties such as:
- `customerId`: `1`
- `name`: `"Alice Johnson"`
- `city`: `"New York"`
- `state`: `""`
- `country`: `"USA"`
- `age`: `29`
- `email`: `"alice.johnson@example.com"`
- `phone`: `""`

---

## Q6. What is Cypher in Neo4j?

**Answer:**
**Cypher** is Neo4j's declarative graph query language (analogous to SQL for relational databases). It uses ASCII-art visual syntax to represent nodes and relationships:
- `(c:Customer)` represents a Node labeled `Customer`.
- `[r:BOUGHT]` represents a Relationship labeled `BOUGHT`.
- `(c:Customer)-[:BOUGHT]->(p:Product)` represents a directed graph pattern.

---

## Q7. How does the official Neo4j Python Driver work?

**Answer:**
The official `neo4j` Python driver connects to the database via the binary **Bolt protocol** (`bolt://neo4j:7687`).

**Execution flow:**
1. **Driver initialization:** `GraphDatabase.driver(uri, auth=(user, password))` maintains a managed connection pool.
2. **Session creation:** `driver.session()` opens a logical session for transaction execution.
3. **Cypher execution:** `session.run(query, parameters)` executes parameterized Cypher statements safely against the database engine.

---

## Q8. Why should Cypher queries always use parameterization (`$CustomerID`) instead of string interpolation?

**Answer:**
1. **Security (Cypher Injection Prevention):** Parameterization prevents Cypher injection attacks where malicious input strings manipulate the query syntax.
2. **Performance (Query Plan Caching):** Neo4j parses and caches execution plans for Cypher queries. Parameterized queries share the same execution plan regardless of input values, significantly reducing parsing overhead.

---

## Q9. What is the clean architecture role of `neo4j_repository.py` vs `graph_loader.py`?

**Answer:**
- **`neo4j_repository.py` (Repository Layer):** Manages low-level database concerns — driver creation, connection retries, Cypher query string definition, parameter binding, session management, and handling database exceptions (`Neo4jError`, `ServiceUnavailable`).
- **`graph_loader.py` (Service Layer):** Manages domain orchestration — receives generic record payloads from the Kafka consumer, determines the entity type, calls repository methods, and handles high-level graph loading logging and error recovery.

---

## Q10. What environment variables configure the Neo4j connection in the loader?

**Answer:**
- `NEO4J_URI`: Connection URI (`bolt://neo4j:7687`).
- `NEO4J_USER` / `NEO4J_USERNAME`: Database user (`neo4j`).
- `NEO4J_PASSWORD`: Database password (`changeme`).

---

## Q11. What happens if Neo4j is temporarily unavailable when a message arrives?

**Answer:**
1. `Neo4jRepository` attempts to connect with exponential backoff retries without terminating the process.
2. If an individual database write fails, `upsert_customer` catches `Neo4jError` / `Exception`, logs an explicit error message (`"Errors | Neo4j Cypher error during Customer upsert"`), and returns `False`.
3. The error is isolated so the Kafka consumer loop does not crash, satisfying the requirement: *"Do not stop Kafka Consumer because one node failed."*

---

## Q12. How do you verify that 20 customer nodes were created in Neo4j?

**Answer:**
By running the Cypher query:
```cypher
MATCH (c:Customer)
RETURN count(c) AS count;
```
If 20 messages were consumed from `customers.csv`, `count(c)` returns `20`.

---

## Q13. How do you retrieve sample Customer nodes in Neo4j Browser or CLI?

**Answer:**
```cypher
MATCH (c:Customer)
RETURN c
LIMIT 5;
```
This returns the visual graph or JSON representation of 5 `:Customer` nodes with all their properties.

---

## Q14. What is a Relationship in Neo4j?

**Answer:**
A **Relationship** is a directed connection between two Nodes that describes how they are related. Like nodes, relationships can have a type (label) and properties.

In future milestones, relationships will connect nodes:
`(:Customer)-[:PLACED]->(:Order)-[:CONTAINS]->(:Product)`

---

## Q15. What is the difference between Bolt and HTTP protocols in Neo4j?

**Answer:**
- **Bolt (`bolt://`, port 7687):** Neo4j's binary protocol designed specifically for database driver connections. High performance, multiplexed, persistent connection pooling.
- **HTTP (`http://`, port 7474):** REST interface used primarily by web applications, administration scripts, and the Neo4j Browser UI.

---

## Q16. What is Index-Free Adjacency in Neo4j?

**Answer:**
Index-Free Adjacency means every node maintains direct physical memory pointers to its adjacent neighbor nodes. When traversing relationships, Neo4j follows raw pointers on disk/RAM without performing global index lookups, ensuring graph traversal performance remains constant regardless of total database size.

---

## Q17. How does field normalization work in `Neo4jRepository`?

**Answer:**
Incoming payload dictionary keys can vary (e.g. `CustomerID` vs `id` vs `customer_id`).
`Neo4jRepository.upsert_customer()` normalizes keys defensively:
```python
customer_id = data.get("CustomerID") or data.get("customerId") or data.get("customer_id") or data.get("id")
```
This guarantees Cypher parameters receive clean, predictable key-value pairs regardless of CSV header variations.

---

## Q18. How does `session.run()` manage database transactions in the driver?

**Answer:**
When calling `with self.driver.session() as session: session.run(query, params)`, the driver automatically opens an implicit transaction, executes the Cypher statement, commits the transaction upon completion, and releases the session connection back to the driver's pool when exiting the context manager.

---

## Q19. What is a Unique Constraint in Neo4j and how does it relate to `MERGE`?

**Answer:**
A Unique Constraint (e.g., `CREATE CONSTRAINT FOR (c:Customer) REQUIRE c.customerId IS UNIQUE`) instructs Neo4j to enforce uniqueness and create a schema index on `customerId`. This optimizes `MERGE` performance from a label scan to a fast index lookup.

---

## Q20. What is the overall pipeline state at the end of Milestone 05?

**Answer:**
The complete data pipeline is now functional end-to-end:
```
CSV Upload (API) ──► Validation ──► Kafka Producer ──► Kafka Topic (customer-data)
                          │
                          ▼
             Kafka Consumer (Loader) ──► GraphLoader ──► Neo4j Repository ──► Neo4j Database (:Customer nodes)
```
The graph database is fully populated with `:Customer` nodes, ready for Cypher querying and chatbot NLP integration in Milestone 06.
