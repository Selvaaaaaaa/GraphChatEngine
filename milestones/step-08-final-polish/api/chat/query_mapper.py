"""
api/chat/query_mapper.py
------------------------
GraphChatEngine – Predefined Cypher Query Mapper

Milestone 06: Graph Query API and Chat Backend

Maps natural language questions to predefined Cypher queries and formats
the query result into a human-readable response string.

Supported Questions:
  1. "How many customers are there?"
  2. "List all customers"
  3. "Show customer 1" (supports dynamic customer ID e.g., "Show customer X")
  4. "Show customers from Chennai" (supports dynamic city filtering)
  5. "Show customers from Coimbatore"
  6. "Show all emails"
  7. "Show all cities"
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class QuerySpec:
    """
    Data class holding Cypher query, parameters, and result formatting function.
    """

    def __init__(
        self,
        cypher: str,
        params: Dict[str, Any],
        formatter: Callable[[List[Dict[str, Any]]], str],
        question_key: str,
    ) -> None:
        self.cypher = cypher
        self.params = params
        self.formatter = formatter
        self.question_key = question_key


class QueryMapper:
    """
    Maps normalized user questions to Cypher specifications.
    """

    @staticmethod
    def _format_count(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "There are 0 customers."
        count = records[0].get("count", 0)
        return f"There are {count} customers."

    @staticmethod
    def _format_customer_list(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No customers found."
        items = []
        for r in records:
            cid = r.get("customerId", "N/A")
            name = r.get("name", "Unknown")
            city = r.get("city", "Unknown")
            items.append(f"{cid}: {name} ({city})")
        return "Customers:\n" + ", ".join(items)

    @staticmethod
    def _format_single_customer(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "Customer not found."
        node = records[0].get("c") or records[0]
        if isinstance(node, dict):
            cid = node.get("customerId") or node.get("id") or "N/A"
            name = node.get("name") or node.get("Name") or "N/A"
            city = node.get("city") or node.get("City") or "N/A"
            country = node.get("country") or node.get("Country") or "N/A"
            email = node.get("email") or node.get("Email") or "N/A"
            age = node.get("age") or node.get("Age") or "N/A"
            return f"Customer {cid}: {name} | Email: {email} | City: {city}, {country} | Age: {age}"
        return f"Customer details: {str(node)}"

    @staticmethod
    def _format_city_customers(records: List[Dict[str, Any]], city_name: str) -> str:
        if not records:
            return f"No customers found from {city_name.capitalize()}."
        names = []
        for r in records:
            node = r.get("c") or r
            if isinstance(node, dict):
                names.append(f"{node.get('name')} (ID: {node.get('customerId')})")
            else:
                names.append(str(node))
        return f"Customers from {city_name.capitalize()}: " + ", ".join(names)

    @staticmethod
    def _format_emails(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No emails found."
        emails = [r.get("email") for r in records if r.get("email")]
        return "Emails: " + ", ".join(emails)

    @staticmethod
    def _format_cities(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No cities found."
        cities = [r.get("city") for r in records if r.get("city")]
        return "Cities: " + ", ".join(cities)

    def map_question(self, question: str) -> Optional[QuerySpec]:
        """
        Match question against supported patterns and return QuerySpec.
        """
        q_norm = question.strip().lower()
        q_clean = re.sub(r"[^\w\s]", "", q_norm)  # Strip punctuation for matching

        # 1. "How many customers are there?"
        if "how many customers" in q_clean or q_clean == "how many customers are there":
            cypher = "MATCH (c:Customer) RETURN count(c) AS count"
            return QuerySpec(cypher, {}, self._format_count, "How many customers are there?")

        # 2. "List all customers"
        if q_clean in ["list all customers", "list customers", "show all customers"]:
            cypher = "MATCH (c:Customer) RETURN c.customerId AS customerId, c.name AS name, c.city AS city ORDER BY toInteger(c.customerId)"
            return QuerySpec(cypher, {}, self._format_customer_list, "List all customers")

        # 3. "Show customer X" (e.g. "Show customer 1")
        match_cust = re.search(r"show customer (\d+)", q_clean)
        if match_cust:
            cust_id = int(match_cust.group(1))
            cypher = "MATCH (c:Customer {customerId: $customerId}) RETURN c"
            return QuerySpec(
                cypher,
                {"customerId": cust_id},
                self._format_single_customer,
                f"Show customer {cust_id}",
            )

        # 4. "Show customers from <city>" (e.g., Chennai, Coimbatore, New York, etc.)
        match_city = re.search(r"show customers from ([a-z\s]+)", q_clean)
        if match_city:
            target_city = match_city.group(1).strip()
            cypher = "MATCH (c:Customer) WHERE toLower(c.city) = $city RETURN c"
            return QuerySpec(
                cypher,
                {"city": target_city},
                lambda recs: self._format_city_customers(recs, target_city),
                f"Show customers from {target_city.capitalize()}",
            )

        # 5. "Show all emails"
        if q_clean in ["show all emails", "list all emails", "get emails"]:
            cypher = "MATCH (c:Customer) RETURN c.email AS email"
            return QuerySpec(cypher, {}, self._format_emails, "Show all emails")

        # 6. "Show all cities"
        if q_clean in ["show all cities", "list all cities", "get cities"]:
            cypher = "MATCH (c:Customer) RETURN DISTINCT c.city AS city"
            return QuerySpec(cypher, {}, self._format_cities, "Show all cities")

        # Unsupported question
        return None
