"""
api/chat/service.py
-------------------
GraphChatEngine – Chat Service Layer

Milestone 06: Graph Query API and Chat Backend

Responsibilities:
  1. Receive user question
  2. Map question to Cypher query using QueryMapper
  3. Execute query via Neo4jChatRepository
  4. Format answer string
  5. Log required execution metrics:
     - Question received
     - Cypher generated
     - Execution time
     - Number of records returned
  6. Return structured response payload
"""

import logging
import time
from typing import Any, Dict

from api.chat.query_mapper import QueryMapper
from api.chat.repository import Neo4jChatRepository, Neo4jChatRepositoryError

logger = logging.getLogger("api.chat.service")

UNSUPPORTED_ANSWER = "Sorry, I can answer only questions about the graph database."


class ChatService:
    """
    Business logic layer for natural language question processing against Neo4j.
    """

    def __init__(self) -> None:
        self.query_mapper = QueryMapper()
        self.repository = Neo4jChatRepository()

    def process_question(self, question: str) -> Dict[str, Any]:
        """
        Process user question and return answer payload.
        """
        start_time = time.perf_counter()

        # Requirement 6: Log Question received
        logger.info("Question received | question='%s'", question)

        query_spec = self.query_mapper.map_question(question)

        # Requirement 3: Return fallback for unsupported questions
        if not query_spec:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Unsupported question | question='%s' | Cypher generated=NONE | Execution time=%.2f ms | Records=0",
                question,
                execution_time_ms,
            )
            return {"answer": UNSUPPORTED_ANSWER}

        # Requirement 6: Log Cypher generated
        logger.info(
            "Cypher generated | question='%s' | cypher='%s' | params=%s",
            question,
            query_spec.cypher,
            query_spec.params,
        )

        try:
            records = self.repository.execute_read(query_spec.cypher, query_spec.params)
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            records_count = len(records)

            # Requirement 6: Log Execution time and Number of records returned
            logger.info(
                "Query executed successfully | Execution time=%.2f ms | Number of records returned=%d",
                execution_time_ms,
                records_count,
            )

            # Format result string
            answer_text = query_spec.formatter(records)

            return {"answer": answer_text}

        except Neo4jChatRepositoryError:
            # Propagate typed repository error to controller
            raise
        except Exception as exc:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Error processing question | question='%s' | error=%s | Execution time=%.2f ms",
                question,
                str(exc),
                execution_time_ms,
            )
            raise Neo4jChatRepositoryError(
                message=f"Error executing graph query: {exc}",
                http_status=500,
            ) from exc

    def close(self) -> None:
        """
        Close underlying repository connections.
        """
        if self.repository:
            self.repository.close()
