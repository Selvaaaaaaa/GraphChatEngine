# REPORT NOTES – Milestone 02: CSV Upload & Validation

> Ready-to-copy bullet points and sections for the project report.

---

## Objective

Milestone 02 implements the **data ingestion entry point** of the GraphChatEngine pipeline. The primary deliverable is a `POST /ingest` REST endpoint that accepts CSV file uploads, performs multi-level validation, extracts structured metadata, and returns a job descriptor JSON object. No data is forwarded to downstream systems (Kafka, Neo4j) in this milestone — the scope is deliberately bounded to validation and metadata extraction.

---

## Architecture

The API follows a layered clean architecture pattern introduced in this milestone:

```
HTTP Request
    │
    ▼
routers/ingest.py          HTTP layer — parse UploadFile, map errors to status codes
    │
    ▼
services/ingest_service.py Business logic — validate, parse, extract, generate job ID
    │
    ├── utils/file_helpers.py    Stateless pure functions (extension check, unit conversion)
    └── Third-party: pandas, uuid, io
    │
    ▼
schemas/ingest.py          Pydantic models — response serialization + Swagger generation
    │
    ▼
HTTP Response (200 / 400 / 422 / 500)
```

Supporting infrastructure:
- `core/config.py` — centralised environment variable access
- `core/logging_config.py` — root logger configuration

---

## Implementation

### Endpoint Design

`POST /ingest` accepts a single `UploadFile` parameter via `multipart/form-data`. FastAPI's `UploadFile` type streams the multipart body asynchronously, keeping the event loop non-blocking. The `python-multipart` library is required for FastAPI to parse multipart bodies.

### Validation Pipeline

Five validation checks are applied in sequence (fail-fast order):

1. **Extension check** — `filename.lower().endswith('.csv')` — O(1), no I/O
2. **Empty file check** — `len(raw_bytes) == 0` — before allocating any parsing structures
3. **Pandas parse** — `pd.read_csv(io.BytesIO(raw_bytes))` — catches malformed content
4. **Header check** — `dataframe.columns.empty` — must have at least one named column
5. **Row check** — `dataframe.empty` — headers-only files are rejected

### Error Handling

A custom `CSVValidationError` exception class carries both a user-facing message and a suggested HTTP status code. The router catches this specifically and converts it to a `JSONResponse`. Generic `Exception` is caught separately and returns HTTP 500. This separation keeps the service layer free of HTTP concerns.

### Metadata Extraction

After passing all validation checks, the following metadata is extracted:
- `rows` — `len(dataframe)` (excludes the header row)
- `columns` — `len(dataframe.columns)`
- `column_names` — `dataframe.columns.tolist()`
- `size_kb` — `round(len(raw_bytes) / 1024, 2)`
- `job_id` — `str(uuid.uuid4())`
- `timestamp` — `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")`

---

## Validation

### Test Cases

| Test Case            | Input              | Expected HTTP | Expected Body                         |
|----------------------|--------------------|---------------|---------------------------------------|
| Valid CSV (15 rows)  | `test.csv`         | 200           | Full metadata JSON with `status: validated` |
| Wrong extension      | `report.pdf`       | 400           | `{"error": "Only CSV files are supported..."}` |
| Empty file           | 0-byte .csv        | 400           | `{"error": "CSV file is empty..."}` |
| Malformed content    | `invalid.csv`      | 422           | `{"error": "Unable to parse CSV..."}` |
| Headers only         | header-only .csv   | 400           | `{"error": "...no data rows..."}` |

### Tools Used

- **Swagger UI** (`/docs`) — interactive testing without any client code
- **curl** — command-line testing for CI/CD integration
- **Docker logs** — verify logging output: `docker compose logs -f api`

---

## Screenshots to Capture

1. **Swagger UI** — `POST /ingest` expanded with the "Try it out" panel visible
2. **Successful response** — HTTP 200 JSON body with all metadata fields populated
3. **Error response** — HTTP 400 for wrong file type
4. **Docker logs** — showing the structured log output (timestamp, level, service, message)
5. **File tree** — VS Code Explorer showing the clean architecture folder structure
6. **Neo4j Browser** — still running (infrastructure unchanged from Milestone 01)

---

## Expected Output

### Happy Path

```
POST /ingest   →   HTTP 200

{
  "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "test.csv",
  "rows": 15,
  "columns": 6,
  "column_names": ["id","name","email","age","city","country"],
  "size_kb": 0.72,
  "status": "validated",
  "timestamp": "2026-07-30T12:34:56.789012"
}
```

### Docker Log Output

```
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Upload started | filename=test.csv
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Validation success | filename=test.csv | rows=15 | columns=6 | size_kb=0.72
2026-07-30T12:34:56 | INFO     | api.services.ingest_service | Job created | job_id=3fa85f64-... | filename=test.csv
```

---

## Challenges

1. **Package import resolution inside Docker** — Using absolute imports (`from api.services...`) requires the `api/` directory to be placed under `/app/api/` and `PYTHONPATH=/app` set in the Dockerfile. This is non-obvious and was a key design decision.

2. **Distinguishing empty files from empty CSVs** — A zero-byte file and a headers-only CSV both appear "empty" but require different error messages. Two separate checks were needed: a byte-count check before pandas, and a `dataframe.empty` check after.

3. **MIME type unreliability** — Browsers send different `Content-Type` values for `.csv` files (`text/csv`, `text/plain`, `application/octet-stream`). Relying solely on MIME type would cause false rejections. The file extension is used as the primary validation signal.

4. **Keeping `main.py` clean** — The temptation to add route handlers directly in `main.py` was resisted in favour of the router pattern, which scales much better as the number of endpoints grows.

---

## Future Scope

| Feature                  | Planned Milestone | Description                                  |
|--------------------------|-------------------|----------------------------------------------|
| Kafka producer           | Milestone 03      | Publish validated rows to `csv-records` topic |
| Job tracking store       | Milestone 04      | In-memory or Redis store for job status      |
| Neo4j entity extraction  | Milestone 04      | Parse CSV columns as graph nodes/edges       |
| Async streaming upload   | Future            | Handle very large CSVs without buffering     |
| File size limit          | Milestone 03      | Reject files exceeding `MAX_UPLOAD_SIZE_MB`  |
| CSV schema inference     | Future            | Auto-detect data types per column            |
| UI upload form           | Milestone 03      | Drag-and-drop file picker in the browser     |
