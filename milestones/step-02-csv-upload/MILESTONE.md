# Milestone 02 – CSV Upload & Validation

## Objective

Implement a production-quality CSV file upload endpoint (`POST /ingest`) within the FastAPI service. The endpoint accepts multipart/form-data, performs multi-level validation, extracts structured metadata using pandas, generates a unique job identifier, and returns a well-formed JSON response. No data is forwarded to Kafka in this milestone — the pipeline stops immediately after successful validation.

---

## Features Completed

- ✅ **Clean Architecture** — `routers/`, `services/`, `schemas/`, `utils/`, `core/` structure
- ✅ **`POST /ingest` endpoint** — multipart/form-data CSV file upload
- ✅ **File-type validation** — extension check (.csv only), rejects .pdf, .xlsx, .png, .jpg, .zip
- ✅ **Empty file detection** — HTTP 400 on zero-byte uploads
- ✅ **Pandas CSV parsing** — catches malformed/corrupted CSV files
- ✅ **Structural validation** — missing headers, no data rows
- ✅ **Metadata extraction** — rows, columns, column names, file size in KB
- ✅ **UUID4 job ID** — unique identifier per upload
- ✅ **ISO-8601 timestamp** — UTC timezone-aware
- ✅ **Typed error responses** — `CSVValidationError` maps to correct HTTP codes
- ✅ **Pydantic schemas** — drive both serialization and Swagger documentation
- ✅ **Python logging** — upload start, validation success/failure, errors
- ✅ **Swagger UI** — `POST /ingest` fully documented with examples
- ✅ **Sample data** — `test.csv` (15 rows) and `invalid.csv` in `sample-data/`
- ✅ **main.py refactored** — zero business logic, router-only pattern

---

## What Works

| Feature                              | Status | Notes                                      |
|--------------------------------------|--------|--------------------------------------------|
| `POST /ingest` with valid CSV        | ✅     | Returns full metadata JSON                 |
| `POST /ingest` with wrong extension  | ✅     | HTTP 400 with descriptive error            |
| `POST /ingest` with empty file       | ✅     | HTTP 400                                   |
| `POST /ingest` with malformed CSV    | ✅     | HTTP 422                                   |
| `POST /ingest` with headers-only CSV | ✅     | HTTP 400 — no data rows                    |
| Swagger UI shows POST /ingest        | ✅     | Full examples, response schemas            |
| Python logging in Docker logs        | ✅     | Visible via `docker compose logs api`      |
| All Milestone 01 endpoints intact    | ✅     | `GET /`, `GET /health` unchanged           |

---

## What Does NOT Work Yet

| Feature                     | Planned Milestone |
|-----------------------------|-------------------|
| Kafka producer              | Milestone 03      |
| Kafka consumer (Loader)     | Milestone 03      |
| Neo4j graph writes          | Milestone 04      |
| Cypher queries              | Milestone 04      |
| Chatbot / NLP interface     | Milestone 05      |
| UI upload form              | Milestone 03      |
| Job tracking / status API   | Milestone 04      |

---

## Architecture

```
POST /ingest (HTTP)
       │
       ▼
api/routers/ingest.py          ← Thin HTTP layer (parse request, map errors to HTTP codes)
       │
       ▼
api/services/ingest_service.py ← Business logic: validate, parse, extract metadata
       │
       ├── api/utils/file_helpers.py   ← Stateless helpers (extension check, KB conversion)
       ├── pandas.read_csv()           ← CSV parsing engine
       └── uuid.uuid4()               ← Job ID generation
       │
       ▼
api/schemas/ingest.py          ← Pydantic models (serialize response, document Swagger)
       │
       ▼
JSON Response (HTTP 200 / 400 / 422 / 500)
```

**Layered design principles:**
- **Router** knows nothing about pandas or UUIDs — only HTTP
- **Service** knows nothing about HTTP status codes — only domain errors
- **Schemas** are shared between serialization and documentation
- **Utils** are stateless, pure functions — easily unit-testable

---

## Commands

```bash
# Rebuild and start (required after code changes)
docker compose up --build

# Test with valid CSV (curl)
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample-data/test.csv"

# Test with wrong extension
curl -X POST http://localhost:8000/ingest \
  -F "file=@README.md"

# Test with malformed CSV
curl -X POST http://localhost:8000/ingest \
  -F "file=@sample-data/invalid.csv"

# View API logs
docker compose logs -f api

# Open Swagger UI
start http://localhost:8000/docs
```

---

## Viva Notes

**Q1. Why use `UploadFile` instead of `bytes`?**
`UploadFile` streams data from the multipart body without loading the entire file into memory at once. It supports async `.read()`, which keeps the event loop non-blocking. `bytes` would require the entire file content upfront.

**Q2. Why pandas for CSV parsing?**
Pandas is the industry-standard library for structured data in Python. It handles edge cases like quoted fields, different delimiters, encoding variants, and BOM markers automatically. It also gives us instant access to `shape`, `columns`, and dtype inference without writing any parsing code.

**Q3. Why UUID4 for job IDs?**
UUID4 is randomly generated, making collisions statistically impossible (2¹²² possible values). It requires no central counter or database lookup to generate, making it safe for distributed systems. It's also URL-safe and widely supported across systems.

**Q4. Why validate the file extension before calling pandas?**
Extension validation is O(1) — it rejects clearly wrong files (`.pdf`, `.xlsx`) immediately without allocating memory or invoking the pandas parser. This is a "fail fast" pattern that saves CPU and avoids unnecessary I/O.

**Q5. Why is `multipart/form-data` used for file uploads?**
`application/json` cannot encode binary file content. `multipart/form-data` is the HTTP standard for mixed payloads (files + form fields). Browsers and curl both support it natively, and FastAPI's `UploadFile` maps directly to it.

**Q6. Why separate `CSVValidationError` from generic `Exception`?**
A custom exception carries both the user-facing message and the HTTP status code. The router catches it specifically and converts it to the correct HTTP response. Generic exceptions fall through to a 500 handler. This separation keeps error handling clean and predictable.

**Q7. Why are Pydantic schemas defined separately from the router?**
Schemas are reusable — the same `IngestSuccessResponse` could be used by multiple routers, tests, and documentation generators. Keeping them in `schemas/` prevents coupling and enables independent testing.

**Q8. Why return `size_kb` instead of `size_bytes`?**
Kilobytes are human-readable for display in UIs and reports. The internal calculation (bytes / 1024) is trivial. Downstream consumers (Kafka, Neo4j) don't need raw byte counts for this use case.

**Q9. Why is `main.py` restricted to router registration only?**
Following the Single Responsibility Principle, `main.py` is the composition root. Mixing business logic here would make it hard to test, extend, or replace components. The router-only pattern is standard in production FastAPI applications.

**Q10. Why log at both INFO and WARNING levels?**
INFO records normal operation (upload started, validation success) — useful for audit trails. WARNING records expected failures (wrong file type, empty file) — useful for monitoring. ERROR is reserved for unexpected failures. This tiered approach makes logs actionable.

---

## Report Notes

- Milestone 02 implements the **ingestion entry point** of the pipeline, turning the infrastructure-only skeleton into a functional data-receiving system.
- The `POST /ingest` endpoint uses **multipart/form-data**, the HTTP standard for file uploads, enabling both browser-based and programmatic (curl/Python) clients.
- **Multi-level validation** is applied in sequence: extension check → byte-count check → pandas parse → structural check. Each level catches a different category of invalid input with a specific HTTP status code (400 or 422).
- **pandas** is used as the CSV parsing engine because it handles encoding variants, quoted fields, and BOM markers automatically, eliminating an entire class of edge-case bugs.
- **UUID4** job identifiers are generated server-side, requiring no database or counter, making the system stateless and horizontally scalable.
- The service layer raises a typed `CSVValidationError` that carries both a human-readable message and an HTTP status code, creating a clean contract between the business logic and the HTTP layer.
- **Pydantic schemas** (`IngestSuccessResponse`, `ErrorResponse`) serve dual purposes: they enforce type safety on response data and automatically populate the Swagger UI with examples and descriptions.
- The **Python logging module** is configured centrally in `core/logging_config.py` and driven by the `LOG_LEVEL` environment variable, making verbosity adjustable without code changes.
- Clean architecture separates concerns across five layers (`routers/`, `services/`, `schemas/`, `utils/`, `core/`) — each layer has a single responsibility and can be tested in isolation.
- The `sample-data/` directory provides two test fixtures: `test.csv` (15 rows, valid) for the happy path and `invalid.csv` (malformed content) for error-path verification.
