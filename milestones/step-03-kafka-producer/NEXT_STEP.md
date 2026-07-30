# Next Step – Milestone 04: Kafka Consumer & Neo4j Integration

## What Milestone 04 Will Implement

Milestone 04 closes the Kafka → Neo4j segment of the pipeline. Messages published to `customer-data` in Milestone 03 will be consumed and written as nodes and relationships in the graph database.

### Features

1. **Kafka Consumer in `loader/kafka_consumer.py`**
   - Subscribe to `customer-data` topic using a consumer group
   - Deserialise each JSON message back to a Python dict
   - Extract `job_id`, `row_number`, and `data` fields
   - Pass `data` to the Neo4j writer

2. **Neo4j Writer in `loader/neo4j_writer.py`**
   - Connect to Neo4j using the `neo4j` Python driver
   - Use `MERGE` Cypher statements to create/update nodes
   - Define relationships based on CSV column semantics:
     - `customers.csv` → `(:Customer)` nodes, `(:City)`, `(:Country)` with `LOCATED_IN` edges
     - `employees.csv` → `(:Employee)` nodes with `REPORTS_TO` edges
     - `orders.csv` → `(:Order)` with `PLACED_BY` and `CONTAINS` edges

3. **Loader Service Rewrite (`loader/loader.py`)**
   - Replace the `while True: sleep(60)` placeholder
   - Start the Kafka consumer loop
   - Route each message to the Neo4j writer based on `job_type` or topic

4. **Loader `requirements.txt`**
   - Add `kafka-python==2.0.2`
   - Add `neo4j==5.19.0`

5. **`GET /jobs/{job_id}` Endpoint (API)**
   - Query Neo4j for all nodes created by a given `job_id`
   - Return count and sample data

---

## Files to Create

| File                              | Purpose                                       |
|-----------------------------------|-----------------------------------------------|
| `loader/kafka_consumer.py`        | Consumer loop — subscribes and processes msgs |
| `loader/neo4j_writer.py`          | Cypher MERGE statements for each entity type  |
| `api/routers/jobs.py`             | `GET /jobs/{job_id}` status endpoint          |

## Files to Modify

| File                              | Change                                        |
|-----------------------------------|-----------------------------------------------|
| `loader/loader.py`                | Replace sleep loop with consumer start        |
| `loader/requirements.txt`         | Add kafka-python, neo4j driver                |
| `api/main.py`                     | Register new `/jobs` router                   |
| `api/requirements.txt`            | Add neo4j==5.19.0                             |

---

## Graph Data Model (Target)

```cypher
(:Customer {id, name, email, age, tier})
  -[:LOCATED_IN]->(:City {name})
  -[:IN_COUNTRY]->(:Country {name})

(:Employee {id, name, role, salary})
  -[:IN_DEPARTMENT]->(:Department {name})
  -[:REPORTS_TO]->(:Employee)

(:Order {order_id, date, total, status})
  -[:PLACED_BY]->(:Customer)
  -[:CONTAINS]->(:Product)

(:Product {id, name, category, price})
  -[:SUPPLIED_BY]->(:Supplier {id})
```

---

## Verify

After Milestone 04, running this Cypher in Neo4j Browser should return results:

```cypher
MATCH (c:Customer)-[:LOCATED_IN]->(city:City)
RETURN c.name, city.name
LIMIT 10
```
