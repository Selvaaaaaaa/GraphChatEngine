"""
loader/services/neo4j_repository.py
-----------------------------------
GraphChatEngine – Neo4j Repository Service

Milestone 05: Neo4j Graph Loader

Responsibilities:
  1. Manage connection lifecycle to Neo4j graph database using official neo4j driver
  2. Read configuration from environment variables (NEO4J_URI, NEO4J_USER/NEO4J_USERNAME, NEO4J_PASSWORD)
  3. Execute Cypher queries using MERGE to insert/update :Customer nodes
  4. Log events: Neo4j Connected, Customer Inserted, Errors
  5. Provide auto-retry / connection error handling
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError, ServiceUnavailable

logger = logging.getLogger("loader.neo4j_repository")


class Neo4jRepository:
    """
    Repository layer for interacting with Neo4j database.
    """

    def __init__(self) -> None:
        self.uri: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self.user: str = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
        self.password: str = os.getenv("NEO4J_PASSWORD", "changeme")

        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self) -> None:
        """
        Connect to Neo4j database with retry logic.
        """
        retry_delay = 2
        max_delay = 30

        while True:
            try:
                logger.info("Connecting to Neo4j | uri=%s | user=%s", self.uri, self.user)
                driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                # Verify connectivity
                driver.verify_connectivity()
                self.driver = driver
                logger.info("Neo4j Connected | uri=%s", self.uri)
                return
            except ServiceUnavailable as exc:
                logger.warning("Neo4j unavailable | error=%s | Retrying in %ds...", str(exc), retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            except Exception as exc:
                logger.error("Error connecting to Neo4j | error=%s | Retrying in %ds...", str(exc), retry_delay)
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)

    def upsert_customer(self, data: Dict[str, Any]) -> bool:
        """
        Insert or update a Customer node using MERGE Cypher query.

        Parameters
        ----------
        data : dict
            Customer attributes dictionary.

        Returns
        -------
        bool
            True if operation succeeded, False otherwise.
        """
        if not self.driver:
            self._connect()

        # Extract normalized attributes handling different key casings
        customer_id = data.get("CustomerID") or data.get("customerId") or data.get("customer_id") or data.get("id")
        if customer_id is None:
            logger.error("Errors | Missing Customer ID in record data: %s", data)
            return False

        name = data.get("Name") or data.get("name") or ""
        city = data.get("City") or data.get("city") or ""
        state = data.get("State") or data.get("state") or ""
        country = data.get("Country") or data.get("country") or ""
        age = data.get("Age") if "Age" in data else data.get("age", 0)
        email = data.get("Email") or data.get("email") or ""
        phone = data.get("Phone") or data.get("phone") or ""

        # Convert non-standard values like NaN/None safely
        params = {
            "CustomerID": int(customer_id) if str(customer_id).isdigit() else str(customer_id),
            "Name": str(name) if name is not None else "",
            "City": str(city) if city is not None else "",
            "State": str(state) if state is not None else "",
            "Country": str(country) if country is not None else "",
            "Age": int(age) if age is not None and str(age).isdigit() else (age if age is not None else 0),
            "Email": str(email) if email is not None else "",
            "Phone": str(phone) if phone is not None else "",
        }

        query = """
        MERGE (c:Customer {customerId: $CustomerID})
        SET c.name = $Name,
            c.city = $City,
            c.state = $State,
            c.country = $Country,
            c.age = $Age,
            c.email = $Email,
            c.phone = $Phone
        RETURN c.customerId AS customerId
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                record = result.single()
                if record:
                    logger.info("Customer Inserted | customerId=%s", record["customerId"])
                    return True
                else:
                    logger.warning("Duplicate Customer Ignored or query completed without record return | customerId=%s", params["CustomerID"])
                    return True
        except Neo4jError as exc:
            logger.error("Errors | Neo4j Cypher error during Customer upsert | customerId=%s | error=%s", params["CustomerID"], str(exc))
            return False
        except Exception as exc:
            logger.error("Errors | Unexpected error during Customer upsert | customerId=%s | error=%s", params["CustomerID"], str(exc))
            return False

    def close(self) -> None:
        """
        Close driver connection cleanly.
        """
        if self.driver:
            try:
                self.driver.close()
                logger.info("Neo4j driver closed cleanly.")
            except Exception as exc:
                logger.warning("Error closing Neo4j driver | error=%s", str(exc))
