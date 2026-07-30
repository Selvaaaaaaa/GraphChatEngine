/**
 * GraphChatEngine – Frontend Chat Application
 * Milestone 07: Frontend Chat Interface
 *
 * Communicates with POST http://localhost:8000/chat
 */

const API_CHAT_URL = "http://localhost:8000/chat";
const API_HEALTH_URL = "http://localhost:8000/health";

let conversationHistory = [];

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  checkBackendHealth();
  // Periodically check backend health every 15s
  setInterval(checkBackendHealth, 15000);
});

/**
 * Check health status of FastAPI backend.
 */
async function checkBackendHealth() {
  const healthDot = document.getElementById("healthDot");
  const healthStatus = document.getElementById("healthStatus");

  try {
    const response = await fetch(API_HEALTH_URL, { signal: AbortSignal.timeout(3000) });
    if (response.ok) {
      healthDot.className = "health-dot online";
      healthStatus.textContent = "API & Neo4j Connected";
    } else {
      healthDot.className = "health-dot offline";
      healthStatus.textContent = "API Unreachable";
    }
  } catch (err) {
    healthDot.className = "health-dot offline";
    healthStatus.textContent = "API Offline";
  }
}

/**
 * Form submit handler.
 */
function handleFormSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("userInput");
  const question = input.value.trim();
  if (question) {
    sendQuestion(question);
  }
}

/**
 * Trigger question from preset chip click.
 */
function askPreset(question) {
  const input = document.getElementById("userInput");
  input.value = question;
  sendQuestion(question);
}

/**
 * Core send question function.
 */
async function sendQuestion(question) {
  const input = document.getElementById("userInput");
  const chatLog = document.getElementById("chatLog");
  const welcomeCard = document.getElementById("welcomeCard");

  // Hide welcome card on first message
  if (welcomeCard) {
    welcomeCard.style.display = "none";
  }

  // Clear user input field
  input.value = "";

  // Append user message
  const timestamp = getCurrentTimestamp();
  appendMessage("user", question, timestamp);

  // Show typing indicator
  showTypingIndicator();
  scrollToBottom();

  const startTime = performance.now();

  try {
    // Send POST request to backend API
    const response = await fetch(API_CHAT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question: question }),
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    const executionTimeMs = (performance.now() - startTime).toFixed(2) + " ms";

    removeTypingIndicator();

    if (!response.ok) {
      let errorMsg = `Server returned status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.error) errorMsg = errorData.error;
      } catch (e) {}

      // Log to browser console as required
      console.log("Question:", question);
      console.log("API Response Error:", errorMsg);
      console.log("Execution time:", executionTimeMs);

      appendMessage("bot", `⚠️ Error: ${errorMsg}`, getCurrentTimestamp());
      scrollToBottom();
      return;
    }

    const data = await response.json();
    const botAnswer = data.answer || "No response text returned.";

    // Requirement: Console log Question, API response, Execution time
    console.log("Question:", question);
    console.log("API Response:", data);
    console.log("Execution time:", executionTimeMs);

    // Save to conversation history
    conversationHistory.push({ question, answer: botAnswer, timestamp });

    // Append bot response
    appendMessage("bot", botAnswer, getCurrentTimestamp());
  } catch (error) {
    const executionTimeMs = (performance.now() - startTime).toFixed(2) + " ms";
    removeTypingIndicator();

    console.log("Question:", question);
    console.log("API Error:", error.message || error);
    console.log("Execution time:", executionTimeMs);

    let friendlyError = "Unable to connect to GraphChatEngine backend (http://localhost:8000/chat). Please ensure the API container is running.";
    if (error.name === "TimeoutError") {
      friendlyError = "Request timed out waiting for Neo4j response. Please try again.";
    }

    appendMessage("bot", `⚠️ ${friendlyError}`, getCurrentTimestamp());
  }

  scrollToBottom();
}

/**
 * Append message bubble to chat log DOM.
 */
function appendMessage(sender, text, timestamp) {
  const chatLog = document.getElementById("chatLog");

  const messageRow = document.createElement("div");
  messageRow.className = `message-row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "👤" : "🤖";

  const bubbleContainer = document.createElement("div");
  bubbleContainer.className = "bubble-container";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = timestamp;

  bubbleContainer.appendChild(bubble);
  bubbleContainer.appendChild(meta);

  messageRow.appendChild(avatar);
  messageRow.appendChild(bubbleContainer);

  chatLog.appendChild(messageRow);
}

/**
 * Show animated typing indicator.
 */
function showTypingIndicator() {
  removeTypingIndicator(); // Ensure no duplicates
  const chatLog = document.getElementById("chatLog");

  const typingRow = document.createElement("div");
  typingRow.className = "message-row bot";
  typingRow.id = "typingRow";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;

  typingRow.appendChild(avatar);
  typingRow.appendChild(indicator);

  chatLog.appendChild(typingRow);
}

/**
 * Remove typing indicator.
 */
function removeTypingIndicator() {
  const typingRow = document.getElementById("typingRow");
  if (typingRow) {
    typingRow.remove();
  }
}

/**
 * Clear chat history and restore welcome screen.
 */
function clearChat() {
  const chatLog = document.getElementById("chatLog");
  conversationHistory = [];
  chatLog.innerHTML = "";

  // Re-create Welcome Card
  const welcomeCard = document.createElement("div");
  welcomeCard.className = "welcome-card";
  welcomeCard.id = "welcomeCard";
  welcomeCard.innerHTML = `
    <div class="bot-avatar">🤖</div>
    <div class="welcome-content">
      <h2>Hello!</h2>
      <p>Ask me questions about the graph database.</p>
      <div class="welcome-chips">
        <button class="welcome-chip" onclick="askPreset('How many customers are there?')">• How many customers are there?</button>
        <button class="welcome-chip" onclick="askPreset('List all customers')">• List all customers</button>
        <button class="welcome-chip" onclick="askPreset('Show customer 1')">• Show customer 1</button>
        <button class="welcome-chip" onclick="askPreset('Show customers from Chennai')">• Show customers from Chennai</button>
      </div>
    </div>
  `;

  chatLog.appendChild(welcomeCard);
  console.log("Chat cleared.");
}

/**
 * Helper: Format current timestamp (HH:MM AM/PM).
 */
function getCurrentTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Scroll chat log to bottom.
 */
function scrollToBottom() {
  const chatLog = document.getElementById("chatLog");
  chatLog.scrollTop = chatLog.scrollHeight;
}
