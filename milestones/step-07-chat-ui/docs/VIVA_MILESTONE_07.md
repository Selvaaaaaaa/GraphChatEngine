# VIVA NOTES – Milestone 07: Frontend Chat Interface

> 20 professional interview questions with detailed answers.
> Covers Frontend Architecture, Vanilla JS DOM manipulation, Fetch API, Async/Await, CORS, UI/UX Glassmorphism design, Error handling, and API integration.

---

## Q1. How does the Frontend Chat Interface communicate with the backend?

**Answer:**
The frontend uses the native browser **Fetch API** (`fetch()`) to issue asynchronous HTTP `POST` requests to `http://localhost:8000/chat`.

The request body is sent as a JSON string:
```json
{ "question": "How many customers are there?" }
```
The backend processes the question against Neo4j and returns a JSON response containing `{"answer": "..."}`, which `app.js` renders as a formatted message bubble in the DOM.

---

## Q2. What is CORS and why is it important for the frontend?

**Answer:**
**CORS (Cross-Origin Resource Sharing)** is a browser security mechanism that restricts web pages from making requests to a different domain, port, or protocol than the one serving the web page.

Because the frontend is served locally (or opened via `file://` / port 3000) and the API runs on port 8000, the browser issues a CORS preflight request (`OPTIONS`). The FastAPI backend handles CORS using `CORSMiddleware` (`allow_origins=["*"]`), allowing the browser to read the JSON response.

---

## Q3. Why build the UI using Vanilla HTML/CSS/JavaScript instead of a heavy framework like React or Angular for this project?

**Answer:**
1. **Zero Build Step & Instant Load:** Vanilla JS requires no node module dependencies, webpack bundlers, or transpilation steps.
2. **Low Memory Overhead:** Ideal for containerized environments and lightweight web deployments.
3. **High Performance DOM Manipulations:** Direct DOM node creation (`document.createElement`) executes with minimal overhead.

---

## Q4. How is conversation history maintained in the frontend?

**Answer:**
`app.js` maintains an in-memory array `conversationHistory = []`.
Whenever a user sends a question and receives a bot answer, an object `{ question, answer, timestamp }` is appended to the array.
Clicking the **Clear Chat** button resets `conversationHistory` and clears the chat log DOM.

---

## Q5. How does the UI handle typing indicators and loading states?

**Answer:**
1. Immediately after the user submits a question, `showTypingIndicator()` appends an animated bot typing bubble containing three bouncing dots (`.typing-dot`).
2. While `fetch()` is pending, input controls are managed and the chat log auto-scrolls to the bottom.
3. Once the response arrives (or error triggers), `removeTypingIndicator()` removes the typing bubble from the DOM before rendering the bot's answer bubble.

---

## Q6. How does the frontend handle API timeouts and network disconnections?

**Answer:**
- **Timeout Handling:** `fetch()` uses `AbortSignal.timeout(10000)` (10-second timeout). If the backend does not respond within 10s, a `TimeoutError` is caught and a friendly warning bubble is rendered (`"Request timed out waiting for Neo4j response"`).
- **Network Offline Handling:** If the API container is stopped or unreachable, `catch` catches the network error and renders `⚠️ Unable to connect to GraphChatEngine backend`.
- **Health Badge:** `checkBackendHealth()` polls `http://localhost:8000/health` every 15s to update the sidebar status dot (`Online` / `Offline`).

---

## Q7. How does auto-scrolling work in the chat window?

**Answer:**
`scrollToBottom()` computes the total scrollable height of the chat log element and assigns it to `scrollTop`:
```js
function scrollToBottom() {
  const chatLog = document.getElementById("chatLog");
  chatLog.scrollTop = chatLog.scrollHeight;
}
```
This guarantees that whenever a new user or bot message is appended, the view automatically scrolls down to display the latest message.

---

## Q8. What CSS design principles were used to achieve the ChatGPT-style aesthetic?

**Answer:**
1. **Dark Glassmorphism:** Semi-transparent dark surfaces (`rgba(30, 41, 59, 0.7)`) with `backdrop-filter: blur(8px)`.
2. **Modern Typography:** Clean sans-serif typography (`Inter` from Google Fonts).
3. **Message Bubble Alignment:** User messages are aligned to the right with a vibrant indigo-blue gradient (`linear-gradient(135deg, #4f46e5, #2563eb)`), while Bot messages are aligned to the left with a dark slate card background.
4. **Interactive Chips:** Quick preset question chips with smooth hover animations (`transform: translateX(4px)`).

---

## Q9. How are timestamps formatted for messages?

**Answer:**
`getCurrentTimestamp()` formats the current browser time into localized 12-hour format (`HH:MM AM/PM`):
```js
function getCurrentTimestamp() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
```

---

## Q10. What metrics are logged to the browser console during chat interactions?

**Answer:**
Per project specifications:
1. `Question`: The exact string submitted by the user.
2. `API Response`: The JSON payload returned from `POST /chat`.
3. `Execution time`: Total round-trip time in milliseconds measured via `performance.now()`.

---

## Q11. How does preset chip selection work?

**Answer:**
Clicking a preset chip button calls `askPreset('question text')`, which populates the text input field, clears the initial welcome message card, and executes `sendQuestion(question)`.

---

## Q12. How does `preventDefault()` work in the form submission handler?

**Answer:**
`event.preventDefault()` prevents the default HTML form submission behavior (which would trigger a full page refresh and URL reload), allowing JavaScript to intercept the submit event and handle API fetching asynchronously via AJAX.

---

## Q13. How are user input strings sanitized in `app.js`?

**Answer:**
- `userInput.value.trim()` strips leading and trailing whitespace.
- Empty or whitespace-only inputs are ignored before making fetch calls.
- `textContent` is used instead of `innerHTML` when creating message text nodes to prevent XSS (Cross-Site Scripting) vulnerabilities.

---

## Q14. What is the role of CSS `@keyframes` in the chatbot interface?

**Answer:**
1. `@keyframes fadeIn`: Fades in and slides up the welcome card on load.
2. `@keyframes messageSlide`: Gives incoming message bubbles a natural slide-up animation.
3. `@keyframes typingBounce`: Animates the three bouncing dots in the typing indicator.

---

## Q15. How does the responsive design adapt to mobile screen sizes?

**Answer:**
Using CSS Media Queries (`@media (max-width: 768px)`):
- On mobile devices, the left sidebar is hidden (`display: none`) to maximize screen space for the chat log.
- A mobile-friendly **Clear Chat** button appears in the top header.
- Message bubbles expand from 80% to 90% max-width.

---

## Q16. What HTTP method and headers are used when querying `POST /chat`?

**Answer:**
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Body:** `JSON.stringify({ question: question })`

---

## Q17. How does the frontend clear chat log and restore the welcome message?

**Answer:**
`clearChat()` resets `conversationHistory = []`, clears `chatLog.innerHTML = ""`, and dynamically re-creates and appends the welcome card HTML structure with interactive chips back into `chatLog`.

---

## Q18. How does `performance.now()` differ from `Date.now()` for timing?

**Answer:**
`performance.now()` returns a high-resolution timestamp measured in milliseconds with sub-millisecond precision, unaffected by system clock adjustments. `Date.now()` returns coarse Unix epoch timestamps susceptible to clock drift.

---

## Q19. How are error messages presented to the user?

**Answer:**
Errors are rendered directly inside a bot message bubble with a warning icon (`⚠️`), styled cleanly so the user receives immediate visual feedback without breaking the application layout.

---

## Q20. What is the complete end-to-end user flow in Milestone 07?

**Answer:**
1. User enters `http://localhost:3000` (or opens `ui/index.html`).
2. App checks backend health -> status badge displays `API & Neo4j Connected`.
3. User types a question or clicks a preset chip.
4. User bubble appears; bot typing indicator animates.
5. `POST /chat` is sent to API -> Cypher query runs against Neo4j -> Answer returned.
6. Typing indicator is replaced by Bot message bubble; console logs metrics.
