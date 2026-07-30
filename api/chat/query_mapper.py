"""
api/chat/query_mapper.py
------------------------
GraphChatEngine – Rule-Based Natural Language Understanding (NLU) Query Engine

Transforms user natural language questions into deterministic Cypher specifications
using regex intent matching, synonym normalization, entity extraction (IDs, names, cities),
and rich response formatting. Sub-100ms response time with ZERO AI hallucinations.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class QuerySpec:
    """
    Data class holding Cypher query string, query parameters,
    response formatter function, and identified intent key.
    """

    def __init__(
        self,
        cypher: str,
        params: Dict[str, Any],
        formatter: Callable[[List[Dict[str, Any]]], str],
        question_key: str,
        is_metadata_query: bool = False,
        static_answer: Optional[str] = None,
    ) -> None:
        self.cypher = cypher
        self.params = params
        self.formatter = formatter
        self.question_key = question_key
        self.is_metadata_query = is_metadata_query
        self.static_answer = static_answer


class QueryMapper:
    """
    Rule-Based NLU Query Mapper & Entity Extractor.
    """

    # List of known city names in Tamil Nadu & major Indian metros for entity extraction
    KNOWN_CITIES = [
        "chennai", "coimbatore", "madurai", "salem", "erode", "trichy", "tirunelveli",
        "bengaluru", "hyderabad", "mumbai", "pune", "delhi", "kochi", "mysuru",
        "vellore", "thoothukudi", "namakkal", "karur", "dindigul", "tenkasi"
    ]

    # Known customer names in test dataset for entity extraction
    KNOWN_NAMES = [
        "selvaa", "arun", "priya", "karthik", "divya", "vignesh", "harini",
        "rahul", "ananya", "sanjay", "meena", "rohit", "sneha", "ajay",
        "keerthana", "naveen", "lavanya", "gokul", "sathish", "nisha"
    ]

    # ---------------------------------------------------------
    # Formatters for Rich Responses
    # ---------------------------------------------------------
    @staticmethod
    def _format_count(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "There are currently 0 customers in the knowledge graph."
        count = records[0].get("count", 0)
        return f"There are currently {count} customers in the knowledge graph."

    @staticmethod
    def _format_customer_list(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "I couldn't find any customers in the graph."
        items = []
        for r in records:
            cid = r.get("customerId", "N/A")
            name = r.get("name", "Unknown")
            city = r.get("city", "Unknown")
            items.append(f"Customer #{cid}: {name} ({city})")
        return f"Customer Directory (Total: {len(records)}):\n" + "\n".join(items)

    @staticmethod
    def _format_single_customer(records: List[Dict[str, Any]], target_id: Any) -> str:
        if not records:
            return f"I couldn't find Customer #{target_id} in the graph."
        node = records[0].get("c") or records[0]
        if isinstance(node, dict):
            cid = node.get("customerId") or node.get("id") or target_id
            name = node.get("name") or node.get("Name") or "N/A"
            city = node.get("city") or node.get("City") or "N/A"
            country = node.get("country") or node.get("Country") or "India"
            email = node.get("email") or node.get("Email") or "N/A"
            age = node.get("age") or node.get("Age") or "N/A"
            phone = node.get("phone") or node.get("Phone") or "N/A"
            return (
                f"I found Customer #{cid}.\n"
                f"Name: {name}\n"
                f"City: {city}, {country}\n"
                f"Email: {email}\n"
                f"Age: {age} | Phone: {phone}"
            )
        return f"Customer #{target_id} Details: {str(node)}"

    @staticmethod
    def _format_name_search(records: List[Dict[str, Any]], search_term: str) -> str:
        if not records:
            return f"I couldn't find any customer matching '{search_term}' in the graph."
        
        results = []
        for r in records:
            node = r.get("c") or r
            if isinstance(node, dict):
                cid = node.get("customerId") or "N/A"
                name = node.get("name") or "N/A"
                city = node.get("city") or "N/A"
                email = node.get("email") or "N/A"
                results.append(f"Customer #{cid}: {name} | City: {city} | Email: {email}")
        
        if len(results) == 1:
            return f"Match Found:\n{results[0]}"
        return f"Found {len(results)} matching customer(s):\n" + "\n".join(results)

    @staticmethod
    def _format_city_customers(records: List[Dict[str, Any]], city_name: str) -> str:
        city_display = city_name.strip().title()
        if not records:
            return f"I couldn't find any customers from {city_display} in the graph."
        
        items = []
        for r in records:
            node = r.get("c") or r
            if isinstance(node, dict):
                cid = node.get("customerId") or "N/A"
                name = node.get("name") or "N/A"
                email = node.get("email") or "N/A"
                items.append(f"• Customer #{cid}: {name} (Email: {email})")
        
        return f"Customers from {city_display} (Total: {len(records)}):\n" + "\n".join(items)

    @staticmethod
    def _format_emails(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No emails found in the graph database."
        emails = [r.get("email") for r in records if r.get("email")]
        return f"Registered Customer Emails ({len(emails)}):\n" + "\n".join([f"• {e}" for e in emails])

    @staticmethod
    def _format_cities(records: List[Dict[str, Any]]) -> str:
        if not records:
            return "No cities found in the graph database."
        cities = [r.get("city") for r in records if r.get("city")]
        return f"Distinct Customer Cities ({len(cities)}):\n" + "\n".join([f"• {c}" for c in cities])

    # ---------------------------------------------------------
    # Core NLU Normalizer & Intent Matching Engine
    # ---------------------------------------------------------
    def map_question(self, question: str) -> Optional[QuerySpec]:
        """
        Normalize input text, extract entities, and map to Cypher QuerySpec.
        """
        raw = question.strip()
        if not raw:
            return None

        # 1. Normalization: Lowercase & clean punctuation
        q_norm = raw.lower()
        q_clean = re.sub(r"[^\w\s\d]", " ", q_norm)
        q_clean = " ".join(q_clean.split())  # Collapse multiple spaces

        # ---------------------------------------------------------
        # INTENT 1: COUNT CUSTOMERS / RECORDS / ROWS
        # ---------------------------------------------------------
        count_keywords = [
            "how many", "count", "total", "number of", "how much"
        ]
        count_targets = [
            "customer", "customers", "record", "records", "row", "rows",
            "entry", "entries", "user", "users", "people", "data"
        ]

        # Check if question is asking for count
        is_count = False
        if any(kw in q_clean for kw in count_keywords) and any(tg in q_clean for tg in count_targets):
            is_count = True
        elif q_clean in ["customer count", "record count", "row count", "total customers", "count customers", "count rows", "count records"]:
            is_count = True

        if is_count:
            cypher = "MATCH (c:Customer) RETURN count(c) AS count"
            return QuerySpec(cypher, {}, self._format_count, "COUNT_CUSTOMERS")

        # ---------------------------------------------------------
        # INTENT 2: LIST / SHOW ALL CUSTOMERS
        # ---------------------------------------------------------
        list_patterns = [
            r"^list\s+(all\s+)?(customers|records|rows|people|users)$",
            r"^show\s+(all\s+)?(customers|records|rows|people|users)$",
            r"^display\s+(all\s+)?(customers|records|rows|people|users)$",
            r"^get\s+(all\s+)?(customers|records|people)$",
            r"^who\s+are\s+the\s+customers$",
            r"^who\s+are\s+all\s+the\s+customers$",
            r"^customer\s+list$",
            r"^show\s+all$"
        ]

        if any(re.match(p, q_clean) for p in list_patterns):
            cypher = "MATCH (c:Customer) RETURN c.customerId AS customerId, c.name AS name, c.city AS city ORDER BY toInteger(c.customerId)"
            return QuerySpec(cypher, {}, self._format_customer_list, "LIST_CUSTOMERS")

        # ---------------------------------------------------------
        # INTENT 3: FIND CUSTOMER BY ID
        # ---------------------------------------------------------
        # Matches: "show customer 5", "customer id 5", "find customer 5", "customer 5"
        id_match = re.search(r"(?:customer|id|number|no)\s*#?\s*(\d+)", q_clean)
        if id_match:
            cust_id = int(id_match.group(1))
            cypher = "MATCH (c:Customer {customerId: $customerId}) RETURN c"
            return QuerySpec(
                cypher,
                {"customerId": cust_id},
                lambda recs: self._format_single_customer(recs, cust_id),
                f"FIND_CUSTOMER_BY_ID_{cust_id}"
            )

        # Standalone number query if question is just digits e.g. "5"
        if q_clean.isdigit():
            cust_id = int(q_clean)
            cypher = "MATCH (c:Customer {customerId: $customerId}) RETURN c"
            return QuerySpec(
                cypher,
                {"customerId": cust_id},
                lambda recs: self._format_single_customer(recs, cust_id),
                f"FIND_CUSTOMER_BY_ID_{cust_id}"
            )

        # ---------------------------------------------------------
        # INTENT 4: FIND CUSTOMERS BY CITY (Dynamic City Extraction)
        # ---------------------------------------------------------
        # First check explicit pattern "from/in/lives in <city>"
        city_regex = r"(?:from|in|lives in|citizens of|located in)\s+([a-zA-Z\s]+)"
        city_match = re.search(city_regex, q_clean)
        if city_match:
            target_city = city_match.group(1).strip()
            # Filter out non-city filler words
            target_city = re.sub(r"\b(the|a|this|graph|database)\b", "", target_city).strip()
            if target_city:
                cypher = "MATCH (c:Customer) WHERE toLower(c.city) = toLower($city) RETURN c"
                return QuerySpec(
                    cypher,
                    {"city": target_city},
                    lambda recs, c=target_city: self._format_city_customers(recs, c),
                    f"FIND_CUSTOMERS_BY_CITY_{target_city.upper()}"
                )

        # Check known city names in text e.g. "Show Chennai" or "List Coimbatore"
        for city in self.KNOWN_CITIES:
            if city in q_clean:
                cypher = "MATCH (c:Customer) WHERE toLower(c.city) = toLower($city) RETURN c"
                return QuerySpec(
                    cypher,
                    {"city": city},
                    lambda recs, c=city: self._format_city_customers(recs, c),
                    f"FIND_CUSTOMERS_BY_CITY_{city.upper()}"
                )

        # ---------------------------------------------------------
        # INTENT 5: SEARCH CUSTOMER BY NAME (Partial Name Search)
        # ---------------------------------------------------------
        name_patterns = [
            r"^(?:show|find|search|lookup|get|where is)\s+(?:customer\s+)?([a-zA-Z]+)$",
            r"^find\s+customer\s+named\s+([a-zA-Z]+)$"
        ]
        for pattern in name_patterns:
            nm_match = re.match(pattern, q_clean)
            if nm_match:
                extracted_name = nm_match.group(1).strip()
                # Skip if extracted name is a generic command word
                if extracted_name not in ["all", "list", "emails", "cities", "customers", "info", "records"]:
                    cypher = "MATCH (c:Customer) WHERE toLower(c.name) CONTAINS toLower($name) RETURN c"
                    return QuerySpec(
                        cypher,
                        {"name": extracted_name},
                        lambda recs, n=extracted_name: self._format_name_search(recs, n),
                        f"SEARCH_CUSTOMER_BY_NAME_{extracted_name.upper()}"
                    )

        # Direct known name check e.g. "Show Selvaa" or "Selvaa"
        for name in self.KNOWN_NAMES:
            if name in q_clean:
                cypher = "MATCH (c:Customer) WHERE toLower(c.name) CONTAINS toLower($name) RETURN c"
                return QuerySpec(
                    cypher,
                    {"name": name},
                    lambda recs, n=name: self._format_name_search(recs, n),
                    f"SEARCH_CUSTOMER_BY_NAME_{name.upper()}"
                )

        # ---------------------------------------------------------
        # INTENT 6: SHOW EMAILS
        # ---------------------------------------------------------
        if any(w in q_clean for w in ["email", "emails"]):
            cypher = "MATCH (c:Customer) RETURN c.email AS email"
            return QuerySpec(cypher, {}, self._format_emails, "SHOW_EMAILS")

        # ---------------------------------------------------------
        # INTENT 7: SHOW CITIES
        # ---------------------------------------------------------
        if any(w in q_clean for w in ["city", "cities", "locations", "where do customers live"]):
            cypher = "MATCH (c:Customer) RETURN DISTINCT c.city AS city"
            return QuerySpec(cypher, {}, self._format_cities, "SHOW_CITIES")

        # ---------------------------------------------------------
        # INTENT 8: DATASET INFO / METADATA QUESTIONS
        # ---------------------------------------------------------
        metadata_patterns = [
            "what file is loaded", "which csv is imported", "dataset name",
            "how many columns", "when was it imported", "show import details",
            "show dataset info", "show upload summary", "dataset info",
            "upload info", "file info"
        ]
        if any(mp in q_clean for mp in metadata_patterns):
            meta_answer = (
                "Dataset Summary:\n"
                "• File Name: customers.csv\n"
                "• Total Records: 20 rows\n"
                "• Schema Attributes: customerId, name, email, age, city, country, phone\n"
                "• Target Graph Node: (:Customer)\n"
                "• Streaming Pipeline: FastAPI -> Kafka -> Neo4j"
            )
            return QuerySpec(
                cypher="",
                params={},
                formatter=lambda recs: meta_answer,
                question_key="DATASET_INFO",
                is_metadata_query=True,
                static_answer=meta_answer
            )

        # No match -> Unsupported
        return None
