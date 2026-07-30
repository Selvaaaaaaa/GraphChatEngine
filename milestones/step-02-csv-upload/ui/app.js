/**
 * GraphChatEngine – UI JavaScript
 * Milestone 01: Project Foundation
 *
 * Currently polls /health to update the status indicator.
 * No upload or chat functionality in this milestone.
 */

/* ------------------------------------------------------------------ */
/* Configuration                                                        */
/* ------------------------------------------------------------------ */

const API_BASE_URL = "http://localhost:8000";
const HEALTH_POLL_INTERVAL_MS = 5000; // 5 seconds

/* ------------------------------------------------------------------ */
/* DOM references                                                       */
/* ------------------------------------------------------------------ */

const statusDot  = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");

/* ------------------------------------------------------------------ */
/* Health-check logic                                                   */
/* ------------------------------------------------------------------ */

/**
 * Fetch /health from the API and update the UI indicator accordingly.
 */
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { method: "GET" });

    if (response.ok) {
      const data = await response.json();
      if (data.status === "ok") {
        setStatus("API Connected – System Ready", true);
        return;
      }
    }

    setStatus("API Responded with Error", false);
  } catch {
    // Network error or API not yet up
    setStatus("System Initializing…", false);
  }
}

/**
 * Update the status card's dot and text.
 *
 * @param {string}  message - Human-readable status message.
 * @param {boolean} ready   - Whether the system is ready (green dot).
 */
function setStatus(message, ready) {
  statusText.textContent = message;

  if (ready) {
    statusDot.classList.add("ready");
  } else {
    statusDot.classList.remove("ready");
  }
}

/* ------------------------------------------------------------------ */
/* Bootstrap                                                            */
/* ------------------------------------------------------------------ */

// Run once immediately, then poll on an interval
checkApiHealth();
setInterval(checkApiHealth, HEALTH_POLL_INTERVAL_MS);
