# VIVA NOTES – UI Enhancement & Dashboard Architecture

> 20 Interview Questions and Technical Answers covering Frontend Dashboard Architecture, FormData, Progress Tracking, Component State, Error Recovery, and REST Integration.

---

## Q1. How does the frontend upload CSV files to the API?

**Answer:**
The frontend uses the `FormData` browser API. When the user selects a `.csv` file and clicks **Upload & Import**, `app.js` creates a `FormData` object, appends `formData.append("file", selectedFile)`, and issues an asynchronous `fetch()` request (`POST http://localhost:8000/ingest`) using multipart encoding.

---

## Q2. How is upload progress animated in the UI?

**Answer:**
`app.js` runs `animatePipelineStage()` during file upload:
- 20%: Uploading CSV file
- 45%: Validating CSV structure
- 70%: Publishing rows to Kafka topic
- 90%: Loading Neo4j graph nodes
- 100%: Pipeline completed

The progress bar width is animated via CSS transitions (`width: 0%` -> `100%`) while active pipeline step icons in the sidebar highlight with glow effects.

---

## Q3. How does the frontend validate file selection before sending?

**Answer:**
`handleFileSelect()` checks:
1. Is a file selected?
2. Does `file.name.toLowerCase().endsWith(".csv")` evaluate to true?

If the file extension is not `.csv`, an alert is shown, the upload button remains disabled, and the input is reset to prevent invalid uploads.

---

## Q4. What happens when the CSV upload succeeds?

**Answer:**
1. The upload form hides and `uploadResult` card appears displaying filename, rows imported, messages published, and a truncated Job ID.
2. The **Dataset Summary** card updates with active dataset metrics.
3. An entry is prepended to **Import History**.
4. A green system success banner is appended to the chat log: `✅ CSV imported successfully! 20 records loaded into Neo4j.`

---

## Q5. How is the system status updated in the sidebar?

**Answer:**
`checkAllSystemStatus()` issues a health probe `fetch("http://localhost:8000/health")` every 15 seconds. If HTTP status is 200 `{"status":"ok"}`, status badges for API Engine, Kafka, Neo4j, and Chat Engine switch to `🟢 Online`. If unreachable, badges switch to `🔴 Offline`.

---

## Q6. How are preset example chips triggered?

**Answer:**
Clicking a preset chip button (e.g. *"Show customers from Chennai"*) fires `askPreset('Show customers from Chennai')`, which populates the text input field, clears the welcome screen, and triggers `sendQuestion()`.

---

## Q7. How does `FormData` differ from sending raw JSON payloads?

**Answer:**
- **JSON Payload (`application/json`):** Used for structured text or objects (like `POST /chat {"question": "..."}`).
- **FormData (`multipart/form-data`):** Encodes binary or text file attachments into MIME boundary blocks, allowing file uploads directly to backend REST endpoints.

---

## Q8. How does `app.js` handle network errors during upload?

**Answer:**
If `POST /ingest` fails or network connection is lost, `catch` catches the exception, hides the progress bar, re-enables the upload button, resets pipeline highlights, and displays an explicit alert modal (`Upload Failed: ...`).

---

## Q9. What CSS technique achieves the dark glassmorphism dashboard theme?

**Answer:**
Semi-transparent background colors (`rgba(30, 41, 59, 0.65)`) combined with backdrop filter blurring (`backdrop-filter: blur(12px)`), thin light border lines (`rgba(255,255,255,0.08)`), and CSS HSL custom property design tokens (`:root`).

---

## Q10. How does the Clear Chat action work?

**Answer:**
`clearChat()` resets `conversationHistory = []`, clears `chatLog.innerHTML = ""`, and dynamically re-creates and appends the initial welcome screen card with example question chips.

---

## Q11. How are timestamps generated for messages and import logs?

**Answer:**
`getCurrentTime()` uses `new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })` to output a clean localized timestamp (e.g. `7:30 PM`).

---

## Q12. How does `scrollTop = scrollHeight` keep the chat log scrolled to the bottom?

**Answer:**
Assigning `chatLog.scrollTop = chatLog.scrollHeight` forces the scrollable container's top offset to match its maximum scrollable height, keeping the latest user or bot message visible.

---

## Q13. How does the frontend prevent double-submitting CSV files?

**Answer:**
Upon submit, `uploadBtn.disabled = true` disables the button immediately while showing the progress bar. It is re-enabled only if the upload fails or if the user clicks **Upload Another File**.

---

## Q14. What metrics are logged to the browser console for chat questions?

**Answer:**
1. `Question`: The question string sent to `POST /chat`.
2. `API Response`: The JSON object received (`{"answer": "..."}`).
3. `Execution time`: Total round-trip time in milliseconds measured with `performance.now()`.

---

## Q15. How does the typing indicator work during chat queries?

**Answer:**
`showTypingIndicator()` appends a bot avatar and a `.typing-wrap` element containing three animated `.typing-dot` elements bouncing via CSS keyframes. It is removed (`removeTypingIndicator()`) when the API response arrives.

---

## Q16. How is the layout optimized for desktop viewports?

**Answer:**
The layout uses a fixed 360px left sidebar alongside a flexible 1fr chat area (`display: flex; height: 100vh; width: 100vw; overflow: hidden;`), creating a responsive desktop dashboard.

---

## Q17. How does the frontend handle empty chat responses?

**Answer:**
If `data.answer` is undefined or empty, `app.js` supplies a fallback string (`"No answer content returned."`) to prevent blank message bubbles.

---

## Q18. How does `AbortSignal.timeout(3000)` improve system monitoring?

**Answer:**
It ensures health probes time out after 3 seconds rather than hanging indefinitely if a backend service hangs or freezes.

---

## Q19. How are drag-and-drop events handled in `setupDragAndDrop()`?

**Answer:**
`preventDefault()` and `stopPropagation()` block browser default file opening behavior. `dragover` adds a border glow class (`dragover`), and `drop` extracts `e.dataTransfer.files` and passes them to `handleFileSelect()`.

---

## Q20. What is the value of combining upload and chat into a single dashboard?

**Answer:**
It eliminates the need for judges or users to switch between terminal commands, Swagger UI, Neo4j Browser, and separate chat windows, providing a seamless end-to-end user experience within a single application.
