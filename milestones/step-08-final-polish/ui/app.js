/**
 * GraphChatEngine – Unified Dashboard & Intelligent NLU Chat Application
 * 
 * Features:
 *   1. CSV Upload & Pipeline Progress (POST http://localhost:8000/ingest)
 *   2. Rule-Based NLU Graph Chat Engine (POST http://localhost:8000/chat)
 *   3. Session Memory for Dataset Questions
 *   4. System Health Probes (GET http://localhost:8000/health)
 */

const API_BASE_URL = "http://localhost:8000";
const INGEST_URL = `${API_BASE_URL}/ingest`;
const CHAT_URL = `${API_BASE_URL}/chat`;
const HEALTH_URL = `${API_BASE_URL}/health`;

let selectedFile = null;
let uploadHistory = [];
let conversationHistory = [];
let activeDataset = null; // Session Memory for active CSV dataset

document.addEventListener("DOMContentLoaded", () => {
  setupDragAndDrop();
  checkAllSystemStatus();
  setInterval(checkAllSystemStatus, 15000);
});

/* =========================================================
   1. SYSTEM STATUS MONITORING
   ========================================================= */
async function checkAllSystemStatus() {
  try {
    const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(3000) });
    setBadgesStatus(res.ok);
  } catch (err) {
    setBadgesStatus(false);
  }
}

function setBadgesStatus(isOnline) {
  const ids = ["stApi", "stKafka", "stNeo4j", "stChat"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      if (isOnline) {
        el.className = "st-badge online";
        el.innerHTML = `<span class="dot"></span> Online`;
      } else {
        el.className = "st-badge offline";
        el.innerHTML = `<span class="dot"></span> Offline`;
      }
    }
  });
}

/* =========================================================
   2. CSV FILE UPLOAD & PIPELINE INTEGRATION
   ========================================================= */
function setupDragAndDrop() {
  const dropArea = document.getElementById("dropArea");
  if (!dropArea) return;

  ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ["dragenter", "dragover"].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add("dragover"), false);
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove("dragover"), false);
  });

  dropArea.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      const fileInput = document.getElementById("csvFileInput");
      fileInput.files = files;
      handleFileSelect({ target: fileInput });
    }
  });
}

function handleFileSelect(event) {
  const file = event.target.files[0];
  const dropText = document.getElementById("dropText");
  const uploadBtn = document.getElementById("uploadBtn");

  if (!file) {
    selectedFile = null;
    dropText.textContent = "Click or Drag CSV File Here";
    uploadBtn.disabled = true;
    return;
  }

  if (!file.name.toLowerCase().endsWith(".csv")) {
    alert("Invalid file extension! Please select a .csv file.");
    selectedFile = null;
    dropText.textContent = "Invalid File! Select a .csv file";
    uploadBtn.disabled = true;
    return;
  }

  selectedFile = file;
  dropText.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  uploadBtn.disabled = false;
}

async function handleCsvUpload(event) {
  event.preventDefault();
  if (!selectedFile) return;

  const uploadBtn = document.getElementById("uploadBtn");
  const progressContainer = document.getElementById("progressContainer");

  uploadBtn.disabled = true;
  progressContainer.classList.remove("hidden");

  // Animate Pipeline Stages
  animatePipelineStage("Uploading...", 20, "pipeCsv", "arrow1");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    await sleep(250);
    animatePipelineStage("Validating CSV Structure...", 45, "pipeCsv", "arrow1");
    
    await sleep(250);
    animatePipelineStage("Publishing Rows to Kafka...", 70, "pipeKafka", "arrow2");

    const response = await fetch(INGEST_URL, {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      let errorText = `HTTP Error ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.error) errorText = errJson.error;
      } catch (e) {}
      throw new Error(errorText);
    }

    const data = await response.json();

    await sleep(250);
    animatePipelineStage("Loading Neo4j Graph Nodes...", 90, "pipeNeo4j", "arrow3");

    await sleep(300);
    animatePipelineStage("Completed!", 100, "pipeChat", "arrow3");

    // Save into Session Memory
    activeDataset = {
      filename: data.filename || selectedFile.name,
      rows: data.rows || 0,
      columns: 8,
      jobId: data.job_id || "N/A",
      timestamp: getCurrentTime()
    };

    // Success Handling
    showUploadSuccess(data);

  } catch (error) {
    progressContainer.classList.add("hidden");
    uploadBtn.disabled = false;
    resetPipelineHighlight();
    alert(`Upload Failed: ${error.message}`);
  }
}

function animatePipelineStage(stageText, percent, activePipeId, activeArrowId) {
  document.getElementById("progressStage").textContent = stageText;
  document.getElementById("progressPercent").textContent = `${percent}%`;
  document.getElementById("progressBar").style.width = `${percent}%`;

  resetPipelineHighlight();
  const pipeEl = document.getElementById(activePipeId);
  const arrowEl = document.getElementById(activeArrowId);
  if (pipeEl) pipeEl.classList.add("active");
  if (arrowEl) arrowEl.classList.add("active");
}

function resetPipelineHighlight() {
  ["pipeCsv", "pipeKafka", "pipeNeo4j", "pipeChat"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
  });
  ["arrow1", "arrow2", "arrow3"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
  });
}

function showUploadSuccess(data) {
  const uploadForm = document.getElementById("uploadForm");
  const uploadResult = document.getElementById("uploadResult");

  uploadForm.classList.add("hidden");
  uploadResult.classList.remove("hidden");

  document.getElementById("resultFilename").textContent = data.filename || selectedFile.name;
  document.getElementById("resultRows").textContent = data.rows || 0;
  document.getElementById("resultMessages").textContent = data.messages_published || 0;
  document.getElementById("resultJobId").textContent = (data.job_id || "N/A").substring(0, 12) + "...";

  // Update Dataset Summary Card
  const datasetSummaryCard = document.getElementById("datasetSummaryCard");
  datasetSummaryCard.classList.remove("hidden");
  document.getElementById("dsName").textContent = data.filename || selectedFile.name;
  document.getElementById("dsRows").textContent = data.rows || 0;
  document.getElementById("dsNodes").textContent = `${data.rows || 0} Nodes`;
  document.getElementById("dsTime").textContent = getCurrentTime();

  // Add to Import History
  addImportHistoryItem(data.filename || selectedFile.name, data.rows || 0);

  // Announce Required Import Summary Card in Chat
  appendImportSummaryCardInChat(data.filename || selectedFile.name, data.rows || 0);
}

function resetUploadForm() {
  selectedFile = null;
  document.getElementById("csvFileInput").value = "";
  document.getElementById("dropText").textContent = "Click or Drag CSV File Here";
  document.getElementById("uploadForm").classList.remove("hidden");
  document.getElementById("uploadResult").classList.add("hidden");
  document.getElementById("progressContainer").classList.add("hidden");
  document.getElementById("progressBar").style.width = "0%";
  document.getElementById("uploadBtn").disabled = true;
  resetPipelineHighlight();
}

function addImportHistoryItem(filename, rows) {
  const historyList = document.getElementById("historyList");
  const emptyHistory = document.getElementById("emptyHistory");
  const historyCount = document.getElementById("historyCount");

  if (emptyHistory) emptyHistory.remove();

  const itemTime = getCurrentTime();
  uploadHistory.push({ filename, rows, time: itemTime });

  historyCount.textContent = uploadHistory.length;

  const item = document.createElement("div");
  item.className = "history-item";
  item.innerHTML = `
    <div>
      <div class="hist-name">📂 ${filename}</div>
      <div class="hist-sub">${rows} Rows • ${itemTime}</div>
    </div>
    <span class="badge-mini">Loaded</span>
  `;

  historyList.prepend(item);
}

/* =========================================================
   3. CHAT NLU ENGINE INTEGRATION (POST /chat)
   ========================================================= */
function handleChatSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("userInput");
  const question = input.value.trim();
  if (question) {
    sendQuestion(question);
  }
}

function askPreset(question) {
  const input = document.getElementById("userInput");
  input.value = question;
  sendQuestion(question);
}

async function sendQuestion(question) {
  const input = document.getElementById("userInput");
  const welcomeCard = document.getElementById("welcomeCard");

  if (welcomeCard) welcomeCard.style.display = "none";

  input.value = "";
  const timestamp = getCurrentTime();

  // Render User Message
  appendMessage("user", question, timestamp);

  // Check Session Memory for local Dataset questions first
  if (activeDataset && isLocalDatasetQuestion(question)) {
    const localAnswer = buildLocalDatasetAnswer(question);
    appendMessage("bot", localAnswer, getCurrentTime());
    scrollToBottom();
    return;
  }

  showTypingIndicator();
  scrollToBottom();

  const startTime = performance.now();

  try {
    const response = await fetch(CHAT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question }),
      signal: AbortSignal.timeout(10000)
    });

    const executionTimeMs = (performance.now() - startTime).toFixed(2) + " ms";
    removeTypingIndicator();

    if (!response.ok) {
      let errText = `HTTP Error ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.error) errText = errJson.error;
      } catch (e) {}

      console.log("Question:", question);
      console.log("API Response Error:", errText);
      console.log("Execution time:", executionTimeMs);

      appendMessage("bot", `⚠️ Error: ${errText}`, getCurrentTime());
      scrollToBottom();
      return;
    }

    const data = await response.json();
    const botAnswer = data.answer || "No answer content returned.";

    // Console Logging Metrics
    console.log("Question:", question);
    console.log("API Response:", data);
    console.log("Execution time:", executionTimeMs);

    conversationHistory.push({ question, answer: botAnswer, timestamp });
    appendMessage("bot", botAnswer, getCurrentTime());

  } catch (error) {
    const executionTimeMs = (performance.now() - startTime).toFixed(2) + " ms";
    removeTypingIndicator();

    console.log("Question:", question);
    console.log("API Error:", error.message || error);
    console.log("Execution time:", executionTimeMs);

    let friendlyError = "Unable to connect to GraphChatEngine Chat API (http://localhost:8000/chat). Please check if backend containers are active.";
    if (error.name === "TimeoutError") {
      friendlyError = "Request timed out waiting for Neo4j response. Please try again.";
    }

    appendMessage("bot", `⚠️ ${friendlyError}`, getCurrentTime());
  }

  scrollToBottom();
}

function isLocalDatasetQuestion(question) {
  const q = question.toLowerCase();
  return (
    q.includes("what file") ||
    q.includes("which csv") ||
    q.includes("dataset name") ||
    q.includes("when was it imported") ||
    q.includes("import details") ||
    q.includes("dataset info") ||
    q.includes("upload summary")
  );
}

function buildLocalDatasetAnswer(question) {
  if (!activeDataset) return "No active dataset loaded in session.";
  return (
    `Dataset Information (Active Session):\n` +
    `• File Name: ${activeDataset.filename}\n` +
    `• Imported Rows: ${activeDataset.rows} rows\n` +
    `• Columns: ${activeDataset.columns} attributes\n` +
    `• Import Time: ${activeDataset.timestamp}\n` +
    `• Job ID: ${activeDataset.jobId}`
  );
}

function appendMessage(sender, text, timestamp) {
  const chatLog = document.getElementById("chatLog");

  const row = document.createElement("div");
  row.className = `msg-row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "👤" : "🤖";

  const wrap = document.createElement("div");
  wrap.className = "bubble-wrap";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const timeEl = document.createElement("div");
  timeEl.className = "msg-time";
  timeEl.textContent = timestamp;

  wrap.appendChild(bubble);
  wrap.appendChild(timeEl);

  row.appendChild(avatar);
  row.appendChild(wrap);

  chatLog.appendChild(row);
}

function appendImportSummaryCardInChat(filename, rows) {
  const chatLog = document.getElementById("chatLog");
  const welcomeCard = document.getElementById("welcomeCard");

  if (welcomeCard) welcomeCard.style.display = "none";

  const cardDiv = document.createElement("div");
  cardDiv.style.cssText = "background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4); color: #f8fafc; padding: 1rem 1.25rem; border-radius: 0.85rem; font-size: 0.9rem; margin: 0.6rem 0; animation: fadeIn 0.3s ease;";
  cardDiv.innerHTML = `
    <div style="font-weight: 800; font-size: 1rem; color: #818cf8; margin-bottom: 0.4rem;">✅ Import Complete</div>
    <div>📁 File: <strong>${filename}</strong></div>
    <div>📊 Imported: <strong>${rows} rows</strong></div>
    <div>🔗 Graph Nodes Created: <strong>${rows} nodes</strong></div>
    <div style="font-size: 0.75rem; color: #34d399; margin-top: 0.4rem;">Ready for graph chat queries!</div>
  `;

  chatLog.appendChild(cardDiv);
  scrollToBottom();
}

function showTypingIndicator() {
  removeTypingIndicator();
  const chatLog = document.getElementById("chatLog");

  const typingRow = document.createElement("div");
  typingRow.className = "msg-row bot";
  typingRow.id = "typingRow";

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = "🤖";

  const wrap = document.createElement("div");
  wrap.className = "typing-wrap";
  wrap.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;

  typingRow.appendChild(avatar);
  typingRow.appendChild(wrap);
  chatLog.appendChild(typingRow);
}

function removeTypingIndicator() {
  const typingRow = document.getElementById("typingRow");
  if (typingRow) typingRow.remove();
}

function clearChat() {
  const chatLog = document.getElementById("chatLog");
  conversationHistory = [];
  chatLog.innerHTML = "";

  const welcomeCard = document.createElement("div");
  welcomeCard.className = "welcome-screen";
  welcomeCard.id = "welcomeCard";
  welcomeCard.innerHTML = `
    <div class="welcome-badge">🤖 GraphChatEngine NLU v0.9</div>
    <h2>Welcome to GraphChatEngine</h2>
    <p>Ask natural language questions about your Neo4j graph database. No strict commands required!</p>
    <div class="welcome-examples">
      <h3>Example Questions</h3>
      <div class="chips-grid">
        <button class="chip-btn" onclick="askPreset('How many customers?')"><span class="chip-icon">📊</span><span>How many customers?</span></button>
        <button class="chip-btn" onclick="askPreset('Show customer 1')"><span class="chip-icon">👤</span><span>Show customer 1</span></button>
        <button class="chip-btn" onclick="askPreset('Show Selvaa')"><span class="chip-icon">🔍</span><span>Show Selvaa</span></button>
        <button class="chip-btn" onclick="askPreset('Show customers from Chennai')"><span class="chip-icon">📍</span><span>Show customers from Chennai</span></button>
        <button class="chip-btn" onclick="askPreset('Dataset info')"><span class="chip-icon">ℹ️</span><span>Dataset info</span></button>
        <button class="chip-btn" onclick="askPreset('Show all cities')"><span class="chip-icon">🏙️</span><span>Show all cities</span></button>
      </div>
    </div>
  `;

  chatLog.appendChild(welcomeCard);
}

function getCurrentTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function scrollToBottom() {
  const chatLog = document.getElementById("chatLog");
  chatLog.scrollTop = chatLog.scrollHeight;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
