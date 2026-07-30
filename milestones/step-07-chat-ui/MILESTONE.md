# Milestone 07 – Frontend Chat Interface

## Objective

Create a professional, responsive ChatGPT-style web interface (`ui/index.html`, `ui/style.css`, `ui/app.js`) that communicates directly with the `POST /chat` backend API, displays user and bot message bubbles with timestamps, maintains conversation history, logs performance metrics to the console, and handles errors gracefully.

---

## Features Completed

- ✅ **`ui/index.html`** — HTML5 layout featuring a left sidebar (brand, pipeline visualization, preset chips, health indicator, clear chat button) and a main chat window (header, log area, welcome card, input bar).
- ✅ **`ui/style.css`** — CSS3 stylesheet with dark glassmorphism, HSL color tokens, Inter typography, rounded bubbles, typing indicator animations, and responsive breakpoints.
- ✅ **`ui/app.js`** — Vanilla JS application logic handling API fetches (`POST /chat`, `GET /health`), DOM message creation, auto-scrolling, preset chip triggers, clear chat functionality, and browser console logging (`Question`, `API Response`, `Execution time`).
- ✅ **`README.md`** — Updated with Frontend section, How to Run, and Screenshots details.
- ✅ **`docs/VIVA_MILESTONE_07.md`** — 20 professional interview Q&As.
- ✅ **`docs/REPORT_MILESTONE_07.md`** — Milestone 07 report notes.

---

## Verification Summary

| Check | Status |
|-------|--------|
| Frontend UI Loading | PASS |
| Backend API Health Connection | PASS |
| Question Submission (`POST /chat`) | PASS |
| Bot Answer Rendering | PASS |
| Timestamp Formatting | PASS |
| Preset Chip Click Trigger | PASS |
| Clear Chat Action | PASS |
| Browser Console Logging | PASS |
| Error Bubble Rendering | PASS |
| Responsive Layout | PASS |
