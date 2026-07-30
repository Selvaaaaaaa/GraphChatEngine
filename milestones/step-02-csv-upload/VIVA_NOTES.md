# VIVA NOTES – Milestone 02: CSV Upload & Validation

> 15 questions with concise, accurate answers. Suitable for technical viva examinations.

---

## Q1. Why use `UploadFile` instead of reading raw `bytes` in the endpoint?

`UploadFile` streams the multipart body asynchronously using Python's async IO. It exposes `.read()` as a coroutine, keeping the Uvicorn event loop non-blocking while the file transfers. Raw `bytes` would force the entire file into memory before the handler executes, which is problematic for large files.

---

## Q2. Why was pandas chosen for CSV parsing over Python's built-in `csv` module?

Pandas handles a superset of CSV edge cases automatically: BOM markers, quoted multiline fields, mixed encodings, and trailing commas. It also provides immediate access to `DataFrame.shape`, `DataFrame.columns`, and dtype inference with a single function call. The built-in `csv` module requires manual handling of all these cases.

---

## Q3. Why generate a UUID4 job ID instead of an auto-incremented integer?

UUID4 is randomly generated with 2¹²² possible values — collisions are statistically impossible. Critically, it requires no shared state (no database, no counter), making the API stateless and safe to run across multiple instances simultaneously. Auto-increment requires a centralised counter, which creates a bottleneck and single point of failure.

---

## Q4. Why validate the file extension before invoking pandas?

The extension check is O(1) — a single `.endswith()` string operation. Rejecting `.pdf` or `.xlsx` files immediately avoids allocating an `io.BytesIO` buffer and running the pandas parser on data that can never be a valid CSV. This is the "fail fast" principle: detect and reject errors as early and cheaply as possible.

---

## Q5. What is `multipart/form-data` and why is it required for file uploads?

`multipart/form-data` is an HTTP encoding scheme that splits a request body into labelled parts, each with its own Content-Type. It is required for file uploads because `application/json` is text-only and cannot represent binary data efficiently. The standard is defined in RFC 7578. Browsers use it for `<input type="file">` and curl uses it with the `-F` flag.

---

## Q6. What HTTP status codes does the endpoint return and why?

| Code | Scenario |
|------|----------|
| 200  | CSV passes all validation — returns job metadata |
| 400  | Wrong extension, empty file, no data rows, missing headers |
| 422  | File extension is .csv but content is unparseable by pandas |
| 500  | Unexpected internal server error |

The distinction between 400 (client error — bad input) and 422 (client error — unprocessable entity) follows RFC 9110 semantics.

---

## Q7. What is `python-multipart` and why must it be in `requirements.txt`?

`python-multipart` is the library FastAPI uses internally to parse `multipart/form-data` request bodies. Without it, FastAPI raises a runtime error when an `UploadFile` parameter is declared. It is a required but non-obvious dependency because it is not bundled with FastAPI itself.

---

## Q8. Why is `CSVValidationError` a custom exception class instead of using `HTTPException`?

`HTTPException` is an HTTP-layer concept. Raising it inside the service layer would create an upward dependency from business logic to the web framework — a clean architecture violation. `CSVValidationError` is a domain-level exception that carries a message and suggested HTTP code. The router translates it to `JSONResponse`. This makes the service layer independently testable without a running web server.

---

## Q9. What does `io.BytesIO` do in the ingest service?

`io.BytesIO` wraps raw bytes in a file-like object that can be passed to `pandas.read_csv()`. Pandas expects either a file path (string) or a file-like object. Since the bytes come from an in-memory HTTP upload rather than a filesystem file, `BytesIO` bridges the gap without writing a temporary file to disk.

---

## Q10. Why is `PYTHONPATH=/app` set in the Dockerfile?

The API source code is copied into `/app/api/` inside the container. For `from api.services.ingest_service import ...` to resolve, Python must be able to find the `api` package. Setting `PYTHONPATH=/app` tells the Python interpreter to look in `/app` when resolving package names, making `/app/api/` discoverable as the `api` package.

---

## Q11. Why is logging configured in `core/logging_config.py` and called once in `main.py`?

Centralising logging configuration ensures a consistent format across all modules. Calling `configure_logging()` once at application startup sets the root logger level and handler — all subsequent `logging.getLogger(__name__)` calls inherit this configuration automatically. If logging were configured per-module, the format could be inconsistent and handlers could multiply.

---

## Q12. What is the difference between a CSV file and an Excel (.xlsx) file?

| Property     | CSV                           | Excel (.xlsx)                   |
|--------------|-------------------------------|---------------------------------|
| Format       | Plain text, comma-separated   | Binary ZIP archive (XML inside) |
| Multi-sheet  | No                            | Yes                             |
| Formulas     | No                            | Yes                             |
| Styles       | No                            | Yes                             |
| Portability  | Universal                     | Requires Excel or openpyxl      |
| Parse cost   | Minimal                       | Higher (XML extraction)         |

CSVs are chosen for this pipeline because they are the simplest interchange format for tabular data.

---

## Q13. Why does the endpoint return `size_kb` instead of `size_bytes`?

File size in bytes is an implementation detail meaningful only to computers. Kilobytes are human-readable and appropriate for display in UIs, dashboards, and reports. The conversion (`bytes / 1024`) is trivial. Additionally, for files in the typical range of a CSV (kilobytes to a few megabytes), KB provides a practical unit with one or two significant digits.

---

## Q14. Why is the router in a separate file (`routers/ingest.py`) rather than in `main.py`?

`main.py` is the composition root — it assembles the application but should contain no business logic. Putting route handlers in `main.py` violates the Single Responsibility Principle. Separate router files allow each feature area to be developed, tested, and reviewed independently. Adding a new endpoint requires only adding a new router file and one `include_router()` call in `main.py`.

---

## Q15. What would happen if two users upload CSVs at the exact same second?

Each upload triggers an independent execution of `process_csv_upload()`. Because `uuid.uuid4()` generates a new random UUID per call with 2¹²² possible values, the probability of two job IDs colliding is negligible. Since the service is currently stateless (no in-memory job store), there is no shared mutable state to cause a race condition. When Kafka and Neo4j are introduced, message ordering and transaction isolation will handle concurrent writes safely.
