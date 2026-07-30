"""
api/chat/service.py
-------------------
GraphChatEngine – Chat Service Layer with Intelligent NLU Fallback

Responsibilities:
  1. Receive user natural language question.
  2. Normalize and map question via QueryMapper.
  3. Return static metadata answer if it's a dataset info question.
  4. Execute Cypher query via Neo4jChatRepository if graph query.
  5. Format rich response strings.
  6. Return smart suggestion guidance if question is unsupported.
  7. Log execution metrics (Question, Cypher, Timing ms, Records count).
"""

import logging
import time
from typing import Any, Dict

from api.chat.query_mapper import QueryMapper
from api.chat.repository import Neo4jChatRepository, Neo4jChatRepositoryError

logger = logging.getLogger("api.chat.service")

SMART_SUGGESTIONS_ANSWER = (
    "I can currently help with questions like:\n"
    "• Customer count\n"
    "• Customer details & search by name/ID\n"
    "• Customers by city\n"
    "• Email addresses & cities\n"
    "• Dataset information\n\n"
    "Try asking:\n"
    "• How many customers are there?\n"
    "• Show customer 1\n"
    "• Show Selvaa\n"
    "• Show customers from Chennai"
)


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

        logger.info("Question received | question='%s'", question)

        query_spec = self.query_mapper.map_question(question)

        # 1. Smart suggestion fallback for unsupported questions
        if not query_spec:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Unsupported question | question='%s' | Cypher=NONE | Execution time=%.2f ms | Records=0",
                question,
                execution_time_ms,
            )
            return {"answer": SMART_SUGGESTIONS_ANSWER}

        # 2. Metadata / Local information questions (No Neo4j query required)
        if query_spec.is_metadata_query:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Metadata question matched | question='%s' | intent='%s' | Execution time=%.2f ms",
                question,
                query_spec.question_key,
                execution_time_ms,
            )
            return {"answer": query_spec.static_answer or query_spec.formatter([])}

        # 3. Cypher Graph Query Execution
        logger.info(
            "Cypher generated | question='%s' | intent='%s' | cypher='%s' | params=%s",
            question,
            query_spec.question_key,
            query_spec.cypher,
            query_spec.params,
        )

        try:
            records = self.repository.execute_read(query_spec.cypher, query_spec.params)
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            records_count = len(records)

            logger.info(
                "Query executed successfully | Execution time=%.2f ms | Records returned=%d",
                execution_time_ms,
                records_count,
            )

            # Format result string
            answer_text = query_spec.formatter(records)

            return {"answer": answer_text}

        except Neo4jChatRepositoryError:
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
