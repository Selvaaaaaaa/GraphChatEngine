# Architecture – Milestone 07: Frontend Chat Interface

```
Browser Web Application (ui/index.html)
        │
        ├── UI State & DOM Controller (ui/app.js)
        │     ├── Health Monitor (GET /health)
        │     ├── Conversation Logger (console.log)
        │     └── Message Renderer (Bubbles & Timestamps)
        │
        ▼
FastAPI Backend (POST http://localhost:8000/chat)
        │
        ▼
Neo4j Knowledge Graph (bolt://neo4j:7687)
```

## Component Architecture

1. **`ui/index.html`**:
   - Sidebar: Brand banner, pipeline visualization (`CSV` → `Kafka` → `Neo4j` → `Chat`), quick preset buttons, system health badge.
   - Main Chat Container: Header connection indicator, chat log container (`#chatLog`), initial welcome card, input form with send button.

2. **`ui/style.css`**:
   - Modern glassmorphism theme using CSS custom properties (`:root`).
   - Flexbox layout for sidebar and chat window.
   - Keyframe animations for slide-in transitions and bouncing typing dots.
   - Media queries adapting layout for screens ≤ 768px.

3. **`ui/app.js`**:
   - Handles `fetch()` API calls to `http://localhost:8000/chat`.
   - Manages typing indicator state (`showTypingIndicator` / `removeTypingIndicator`).
   - Implements auto-scrolling (`scrollTop = scrollHeight`).
   - Captures high-resolution execution timing using `performance.now()`.
   - Logs `Question`, `API Response`, and `Execution time` to browser console.
