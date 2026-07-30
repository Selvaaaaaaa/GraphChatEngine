# REPORT NOTES – Milestone 07: Frontend Chat Interface

> Comprehensive report documentation for Milestone 07 covering frontend architecture, UI/UX glassmorphism design, application workflow, testing verification, and required screenshots.

---

## Objective

The objective of Milestone 07 was to build a state-of-the-art, responsive **Frontend Chat Interface** (`ui/index.html`, `ui/style.css`, `ui/app.js`) that communicates directly with the `POST /chat` backend API endpoint.

The interface replicates a ChatGPT-like user experience customized specifically for querying the Neo4j Knowledge Graph.

---

## Architecture & Communication Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Browser Frontend UI                             │
│                  (ui/index.html, style.css, app.js)                    │
│                                                                        │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │ Sidebar & Preset Chips    │      │ Chat Window & Input Form    │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  │                                   │
                  │ (Preset Click)                    │ (POST /chat)
                  ▼                                   ▼
        ┌──────────────────────────────────────────────────┐
        │                FastAPI API                       │
        │          (http://localhost:8000/chat)            │
        └─────────────────────────┬────────────────────────┘
                                  │
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │             Neo4j Graph Database                 │
        │             (bolt://neo4j:7687)                  │
        └──────────────────────────────────────────────────┘
```

---

## UI/UX Design

### Aesthetics & Tokens
- **Theme:** Dark glassmorphism with HSL tailored color palettes and gradients.
- **Typography:** `Inter` font family from Google Fonts for maximum readability.
- **Message Bubbles:**
  - **User Messages:** Aligned right, styled with indigo-blue gradient background (`linear-gradient(135deg, #4f46e5, #2563eb)`).
  - **Bot Messages:** Aligned left, styled with slate card background and bot avatar.
- **Animations:**
  - Bouncing typing indicator dots.
  - Message slide-up transition.
  - Pulsing health indicator dot (`Online` / `Offline`).

### Layout Sections
1. **Left Sidebar:** Brand title, pipeline step visualization (`CSV` → `Kafka` → `Neo4j` → `Chat`), quick preset question chips, API health status indicator, and Clear Chat button.
2. **Main Chat Area:** Header with connection indicator, scrollable conversation container (`#chatLog`), initial welcome card with clickable preset chips, and bottom fixed input bar with send button.

---

## Application Workflow

1. **Initialization:** On page load, `app.js` issues a `fetch` request to `http://localhost:8000/health`. The sidebar health badge updates to `API & Neo4j Connected` (green pulse).
2. **User Input:** User types a question or clicks a preset chip ("How many customers are there?").
3. **DOM Update (User):** User message bubble is rendered with timestamp. Input field is cleared.
4. **Loading State:** Animated typing bubble (`🤖` + 3 bouncing dots) is appended to chat log.
5. **API Fetch:** Asynchronous `POST http://localhost:8000/chat` request is sent with `{"question": "..."}`.
6. **Console Logging:** Question string, API response object, and round-trip execution time (`performance.now()`) are logged to browser console.
7. **DOM Update (Bot):** Typing indicator is removed and bot message bubble displaying the answer is rendered. View auto-scrolls to bottom.
8. **Error Recovery:** If API is offline or returns error status, a red warning bubble is rendered without breaking the layout.

---

## Screenshots Required

1. **Frontend Welcome Screen:** Complete layout showing sidebar, pipeline visualization, preset chips, and bot welcome card.
2. **Interactive Conversation:** Chat log displaying user questions and bot responses ("There are 20 customers.", "List all customers", etc.).
3. **Browser Console Output:** Console displaying logged `Question`, `API Response`, and `Execution time`.
4. **Responsive Mobile View:** Mobile viewport showing single-column chat interface with header clear button.
