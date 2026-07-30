"""
loader/services/graph_loader.py
--------------------------------
GraphChatEngine – Graph Loader Service

Milestone 05: Neo4j Graph Loader

Responsibilities:
  1. Service layer linking Kafka Consumer processing to Neo4j Repository
  2. Orchestrate node creation for ingested record payloads
  3. Provide error handling so node failure does not interrupt the consumer pipeline
  4. Log events: Creating Customer Node, Customer Inserted, Graph Loader Success, Errors
"""

import logging
from typing import Any, Dict

from services.neo4j_repository import Neo4jRepository

logger = logging.getLogger("loader.graph_loader")


class GraphLoader:
    """
    Graph Loader service for creating and updating nodes in Neo4j.
    """

    def __init__(self) -> None:
        self.repository = Neo4jRepository()

    def process_record(self, data: Dict[str, Any]) -> bool:
        """
        Process incoming dictionary data and insert into Neo4j graph.

        Parameters
        ----------
        data : dict
            Message data payload.

        Returns
        -------
        bool
            True if graph insertion succeeded, False otherwise.
        """
        try:
            logger.info("Creating Customer Node | data=%s", data)
            success = self.repository.upsert_customer(data)
            if success:
                logger.info("Graph Loader Success | Customer processed successfully.")
                return True
            else:
                logger.error("Errors | Graph Loader failed to insert customer record.")
                return False
        except Exception as exc:
            logger.error("Errors | Unexpected error in GraphLoader | error=%s", str(exc))
            return False

    def close(self) -> None:
        """
        Close underlying repository connections.
        """
        if self.repository:
            self.repository.close()
