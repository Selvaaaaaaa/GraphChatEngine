"""
api/chat/repository.py
----------------------
GraphChatEngine – Neo4j Read Repository for Chat Service

Milestone 06: Graph Query API and Chat Backend

Handles execution of Cypher read queries against the Neo4j Graph Database.
Reads configuration from api.core.config.settings.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase, Driver
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from api.core.config import settings

logger = logging.getLogger("api.chat.repository")


class Neo4jChatRepositoryError(Exception):
    """
    Exception raised when Neo4j query execution fails.
    """

    def __init__(self, message: str, http_status: int = 503) -> None:
        super().__init__(message)
        self.message = message
        self.http_status = http_status


class Neo4jChatRepository:
    """
    Read-only repository for querying Neo4j Knowledge Graph.
    """

    def __init__(self) -> None:
        self.uri: str = settings.neo4j_uri
        self.user: str = settings.neo4j_user
        self.password: str = settings.neo4j_password
        self.driver: Optional[Driver] = None

    def _get_driver(self) -> Driver:
        """
        Get or initialize Neo4j driver connection.
        """
        if self.driver is None:
            try:
                logger.info("Initializing Neo4j driver for API Chat | uri=%s", self.uri)
                driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
                driver.verify_connectivity()
                self.driver = driver
                logger.info("Neo4j Connected for Chat API | uri=%s", self.uri)
            except ServiceUnavailable as exc:
                logger.error("Neo4j database unavailable | uri=%s | error=%s", self.uri, str(exc))
                raise Neo4jChatRepositoryError(
                    message="Neo4j graph database is unavailable. Please check if the database container is running.",
                    http_status=503,
                ) from exc
            except Exception as exc:
                logger.error("Failed to connect to Neo4j | error=%s", str(exc))
                raise Neo4jChatRepositoryError(
                    message=f"Failed to connect to Neo4j graph database: {exc}",
                    http_status=503,
                ) from exc
        return self.driver

    def execute_read(self, cypher: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute a Cypher read query and return list of result records as dictionaries.
        """
        driver = self._get_driver()
        records_list: List[Dict[str, Any]] = []

        try:
            with driver.session() as session:
                result = session.run(cypher, params)
                for record in result:
                    # Convert Neo4j Record to dict, handling Node objects if present
                    record_dict = {}
                    for key, val in record.data().items():
                        record_dict[key] = val
                    records_list.append(record_dict)
            return records_list
        except Neo4jError as exc:
            logger.error("Cypher execution error | cypher=%s | error=%s", cypher, str(exc))
            raise Neo4jChatRepositoryError(
                message=f"Cypher query execution error: {exc.message}",
                http_status=500,
            ) from exc
        except Exception as exc:
            logger.error("Unexpected error executing Cypher | cypher=%s | error=%s", cypher, str(exc))
            raise Neo4jChatRepositoryError(
                message=f"Unexpected error querying graph database: {exc}",
                http_status=500,
            ) from exc

    def close(self) -> None:
        """
        Close Neo4j driver session connection pool.
        """
        if self.driver:
            try:
                self.driver.close()
                self.driver = None
                logger.info("Neo4j Chat API driver closed cleanly.")
            except Exception as exc:
                logger.warning("Error closing Neo4j Chat API driver | error=%s", str(exc))
