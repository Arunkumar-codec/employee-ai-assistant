// Employee AI Assistant — frontend logic (Day 1 foundation)
//
// WHAT: Talks to the FastAPI backend over plain HTTP fetch calls.
// WHY:  Assessment requires frontend <-> backend communication via HTTP APIs
//       (no framework mandated); vanilla JS keeps Day 1 dependency-free.
//
// Change API_BASE_URL below if the backend runs on a different host/port.
const API_BASE_URL = "http://localhost:8000/api";

const chatWindow = document.getElementById("chat-window");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const employeeIdInput = document.getElementById("employee-id");
const backendStatus = document.getElementById("backend-status");
const errorBanner = document.getElementById("error-banner");

function setBackendStatus(state, label) {
  backendStatus.textContent = `Backend: ${label}`;
  backendStatus.className = `status status--${state}`;
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
}

function clearError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

function appendMessage(role, text) {
  const el = document.createElement("div");
  el.className = `message message--${role}`;
  el.textContent = text;
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return el;
}

function appendMetaBlock(sources, toolsUsed) {
  const el = document.createElement("div");
  el.className = "meta-block";
  const sourcesText = sources.length ? sources.join(", ") : "none";
  const toolsText = toolsUsed.length ? toolsUsed.join(", ") : "none";
  el.innerHTML = `<strong>Sources:</strong> ${sourcesText} &nbsp;|&nbsp; <strong>Tools used:</strong> ${toolsText}`;
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    setBackendStatus("ok", `connected (${data.service})`);
  } catch (err) {
    setBackendStatus("error", "unreachable");
    showError(
      "Could not reach the backend. Make sure it is running (see README) and CORS/FRONTEND_ORIGIN is configured correctly."
    );
  }
}

async function sendMessage() {
  const message = messageInput.value.trim();
  const employeeId = employeeIdInput.value.trim();

  if (!message) return;
  if (!employeeId) {
    showError("Please enter an Employee ID.");
    return;
  }

  clearError();
  appendMessage("user", message);
  messageInput.value = "";
  sendButton.disabled = true;

  const loadingEl = appendMessage("loading", "Thinking…");

  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ employee_id: employeeId, message }),
    });

    if (!res.ok) {
      throw new Error(`Backend returned status ${res.status}`);
    }

    const data = await res.json();
    loadingEl.remove();
    appendMessage("assistant", data.answer);
    appendMetaBlock(data.sources || [], data.tools_used || []);
  } catch (err) {
    loadingEl.remove();
    showError(`Request failed: ${err.message}`);
  } finally {
    sendButton.disabled = false;
  }
}

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendMessage();
});

checkBackendHealth();
