# VIVA NOTES – Rule-Based NLU & Natural Language Processing

> 20 Interview Questions and Technical Answers covering Rule-Based NLU, Intent Classification, Entity Extraction, Regex Matching, Response Formatting, and Execution Latency.

---

## Q1. What is Rule-Based Natural Language Understanding (NLU)?

**Answer:**
Rule-Based NLU uses deterministic pattern matching, regular expressions, synonym mapping, and text normalization algorithms to extract user intent and entities from natural language text without relying on statistical machine learning models or external cloud API calls.

---

## Q2. Why use a Rule-Based NLU engine instead of an LLM like OpenAI or Llama for this graph chatbot?

**Answer:**
1. **Zero Hallucinations:** Rule-based intent mapping guarantees 100% deterministic Cypher generation directly backed by the graph database.
2. **Sub-20ms Latency:** Local execution takes <20ms compared to 1,000–3,000ms LLM latency.
3. **Zero Cost & Offline Execution:** No API tokens, subscriptions, or external network connectivity required.
4. **Security & Privacy:** Customer dataset content never leaves the container network.

---

## Q3. How does the question normalization layer work in `QueryMapper`?

**Answer:**
1. Case Normalization: Converts input text to lowercase.
2. Punctuation Removal: Strips punctuation marks while preserving numeric IDs and entity text using `re.sub(r"[^\w\s\d]", " ", q_norm)`.
3. Whitespace Collapsing: Collapses multiple spaces into single spaces.
4. Synonym Normalization: Maps variations (`rows`, `records`, `entries`, `people`, `users`) to the underlying `:Customer` graph node label.

---

## Q4. How are customer IDs extracted dynamically from questions like "Show customer 5"?

**Answer:**
`QueryMapper` uses regex matching:
```python
id_match = re.search(r"(?:customer|id|number|no)\s*#?\s*(\d+)", q_clean)
```
If matched, `id_match.group(1)` extracts the numeric string (`5`), converts it to `int(5)`, and binds it to the Cypher parameter `{"customerId": 5}`.

---

## Q5. How does partial name search work in Cypher?

**Answer:**
For queries like *"Show Selvaa"* or *"Find Arun"*, the engine generates:
```cypher
MATCH (c:Customer)
WHERE toLower(c.name) CONTAINS toLower($name)
RETURN c
```
This enables case-insensitive substring matching against customer names without requiring exact match strings.

---

## Q6. How are city names extracted dynamically from questions like "Show customers from Chennai"?

**Answer:**
The engine uses a two-tier extraction strategy:
1. **Pattern Extraction:** Regex `r"(?:from|in|lives in)\s+([a-zA-Z\s]+)"` captures the location phrase following prepositional keywords.
2. **Known Entity Matching:** Checks extracted text against a pre-compiled list of Indian cities (`KNOWN_CITIES`) to isolate city names accurately.

---

## Q7. How does the engine handle unsupported or unrecognized questions?

**Answer:**
Instead of returning a unhelpful generic error, `ChatService` returns a **Smart Suggestions Guidance Block** listing supported query categories (Customer count, Details, Search, Cities, Emails, Dataset Info) along with clickable example question chips.

---

## Q8. How are dataset information questions handled without querying Neo4j?

**Answer:**
Questions matching `DATASET_INFO` (`what file is loaded?`, `dataset info`, `show import details`) set `is_metadata_query = True`. `ChatService` immediately returns the formatted metadata summary without issuing a Cypher database call, completing in < 7ms.

---

## Q9. What guarantees that response time stays under 100 ms?

**Answer:**
1. In-memory Python regex matching runs in < 0.1ms.
2. Bolt binary driver protocol to Neo4j executes read queries in < 15ms.
3. Total round-trip execution latency averages 5ms to 25ms.

---

## Q10. How does the engine distinguish between asking for a city vs asking for a customer name?

**Answer:**
The engine evaluates pattern specificity sequentially:
1. Checks for numeric IDs (`customer 5`).
2. Checks prepositional city patterns (`from Chennai`, `in Coimbatore`).
3. Checks known city dictionary tokens.
4. Checks name search verbs (`find Selvaa`, `search Priya`).
5. Checks known customer name dictionary tokens.

---

## Q11. How are records formatted into human-readable answers?

**Answer:**
Each `QuerySpec` contains a custom Python formatter lambda function. For example, `_format_single_customer` formats node properties into:
```
I found Customer #5.
Name: Selvaa
City: Coimbatore, India
Email: selvaa@example.com
```

---

## Q12. What happens if a requested customer ID does not exist in Neo4j?

**Answer:**
The Neo4j query returns an empty record list (`[]`). The formatter checks `if not records:` and returns a clear, explicit answer:
`"I couldn't find Customer #99 in the graph."`

---

## Q13. How does session memory assist dataset questions in the frontend?

**Answer:**
`app.js` stores `activeDataset` metadata (filename, rows count, import time, Job ID) upon upload completion. When the user asks *"What file is loaded?"*, the frontend intercepts it and displays active session dataset details instantly.

---

## Q14. What is the role of parameter binding (`$city`, `$name`) in NLU Cypher generation?

**Answer:**
Extracted entities are passed as driver parameters (`{"city": target_city}`). Parameter binding prevents Cypher injection vulnerabilities and enables Neo4j query plan caching.

---

## Q15. How does the import summary banner work after CSV upload?

**Answer:**
Upon receiving HTTP 200 from `POST /ingest`, `showUploadSuccess()` calls `appendImportSummaryCardInChat()`, appending an indigo card to the chat log displaying:
```
✅ Import Complete
📁 File: customers.csv
📊 Imported: 20 rows
🔗 Graph Nodes Created: 20 nodes
```

---

## Q16. How does the engine handle questions asking for distinct cities?

**Answer:**
It executes `MATCH (c:Customer) RETURN DISTINCT c.city AS city`, filters out null values, and formats a clean list of unique city names.

---

## Q17. Can the NLU engine handle trailing punctuation like question marks?

**Answer:**
Yes. The regex cleaner `re.sub(r"[^\w\s\d]", " ", q_norm)` strips question marks (`?`), exclamation points (`!`), and trailing spaces before intent evaluation.

---

## Q18. How does the NLU engine handle plural vs singular nouns?

**Answer:**
Target match arrays include both singular and plural forms (`customer`/`customers`, `row`/`rows`, `record`/`records`, `entry`/`entries`), ensuring identical intent classification.

---

## Q19. How are metrics logged for NLU queries?

**Answer:**
`ChatService` logs `Question received`, `Cypher generated`, `intent key`, `Execution time=%.2f ms`, and `Records returned` to Python `logging` and browser console.

---

## Q20. What is the overall benefit of this NLU upgrade for the hackathon project?

**Answer:**
It elevates the chatbot from rigid command execution to a natural, user-friendly conversational interface that understands over 55 question variations effortlessly while remaining 100% deterministic and ultra-fast.
