const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

const loginScreen = document.getElementById("login-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const healthMonitor = document.getElementById("health-monitor");
const loginBtn = document.getElementById("loginBtn");
const openAiBtn = document.getElementById("openAiBtn");
const aiWidget = document.getElementById("ai-widget");
const chatBox = document.getElementById("chatBox");
const widgetChatBox = document.getElementById("widgetChatBox");
const aiInput = document.getElementById("aiInput");
const widgetInput = document.getElementById("widgetInput");
const monitorBox = document.getElementById("monitorBox");
const serverStatus = document.getElementById("serverStatus");
const aiStatus = document.getElementById("aiStatus");
const sendAi = document.getElementById("sendAi");
const sendWidgetAi = document.getElementById("sendWidgetAi");
const logoutBtn = document.getElementById("logoutBtn");
const launchBtn = document.getElementById("launchBtn");
const checkBtn = document.getElementById("checkBtn");
const closeAi = document.getElementById("closeAi");

let healthRetryCount = 0;

function showDashboard() {
  loginScreen.classList.add("hidden");
  dashboardScreen.classList.remove("hidden");
  openAiBtn.classList.remove("hidden");
}

function showLogin() {
  loginScreen.classList.remove("hidden");
  dashboardScreen.classList.add("hidden");
  openAiBtn.classList.add("hidden");
  aiWidget.classList.add("hidden");
}

function showNotice(message, isError = false) {
  healthMonitor.className = isError ? "status-box warning" : "status-box success";
  healthMonitor.innerHTML = message;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 12000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      mode: "cors",
      signal: controller.signal
    });
    return response;
  } finally {
    clearTimeout(timer);
  }
}

async function pollHealth() {
  try {
    const start = Date.now();
    const res = await fetchWithTimeout(`${API_BASE_URL}/health`, {}, 12000);

    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }

    const data = await res.json();
    const elapsed = Date.now() - start;

    healthRetryCount = 0;
    showNotice(
      `<i class="fa-solid fa-circle-check"></i> RENDER SERVER ONLINE (Uptime: ${data.uptime}s, ${elapsed}ms)`,
      false
    );

    serverStatus.innerText = "ONLINE";
    aiStatus.innerText = data.ai_connected ? "READY" : "API KEY MISSING";

    monitorBox.innerHTML = `
      <strong>Status:</strong> ${data.status}<br>
      <strong>Version:</strong> ${data.version}<br>
      <strong>Uptime:</strong> ${data.uptime}s<br>
      <strong>AI Connected:</strong> ${data.ai_connected ? "YES" : "NO"}<br>
      <strong>Latency:</strong> ${elapsed}ms
    `;
  } catch (e) {
    healthRetryCount++;
    serverStatus.innerText = "OFFLINE";
    aiStatus.innerText = "STANDBY";
    showNotice(
      `<i class="fa-solid fa-triangle-exclamation"></i> SERVER WAKING UP... PLEASE WAIT`,
      true
    );

    monitorBox.innerHTML = `
      <strong>Status:</strong> WAKING UP<br>
      <strong>Retry:</strong> ${healthRetryCount}<br>
      <strong>Note:</strong> Render may be sleeping. Retrying automatically...
    `;
  }
}

function appendMessage(container, text, type) {
  const div = document.createElement("div");
  div.className = `msg ${type}`;
  div.innerHTML = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addTyping(container) {
  const id = `typing-${Date.now()}`;
  const div = document.createElement("div");
  div.className = "msg ai";
  div.id = id;
  div.innerHTML = `<i class="fa-solid fa-ellipsis fa-fade"></i>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function getToken() {
  return sessionStorage.getItem("anis_jwt") || "";
}

function setToken(token) {
  sessionStorage.setItem("anis_jwt", token);
}

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const humanCheck = document.getElementById("humanCheck").checked;

  if (!humanCheck) {
    showNotice("Please verify identity first.", true);
    return;
  }

  if (!username || !password) {
    showNotice("Render URL and password are required.", true);
    return;
  }

  loginBtn.disabled = true;
  loginBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> CONNECTING SECURE TUNNEL...`;

  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  formData.append("captcha_verified", "true");

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded"
      },
      body: formData
    }, 15000);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "Authentication Failed.");
    }

    setToken(data.access_token);
    showNotice("Access Key Authorized. Unlocking Terminal.", false);

    setTimeout(() => {
      showDashboard();
      pollHealth();
    }, 900);
  } catch (err) {
    console.error("Login error:", err);
    showNotice(err.message || "Failed to fetch.", true);
  } finally {
    loginBtn.disabled = false;
    loginBtn.innerHTML = `<i class="fa-solid fa-power-off"></i> INITIATE CONNECTION`;
  }
});

async function sendAiMessage(container, inputEl) {
  const text = inputEl.value.trim();
  if (!text) return;

  appendMessage(container, text, "user");
  inputEl.value = "";

  const typingId = addTyping(container);

  try {
    const token = getToken();
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ message: text })
    }, 20000);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.detail || "AI request failed.");
    }

    const reply = data.reply || "No AI response returned.";

    const target = document.getElementById(typingId);
    if (target) {
      target.innerHTML = window.marked ? marked.parse(reply) : reply;
    }
  } catch (e) {
    const target = document.getElementById(typingId);
    if (target) {
      target.innerHTML = `<span style="color:var(--danger)">Connection to AI Core severed.</span>`;
    }
  }
}

sendAi.addEventListener("click", () => sendAiMessage(chatBox, aiInput));
sendWidgetAi.addEventListener("click", () => sendAiMessage(widgetChatBox, widgetInput));

aiInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendAiMessage(chatBox, aiInput);
});

widgetInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendAiMessage(widgetChatBox, widgetInput);
});

logoutBtn.addEventListener("click", () => {
  sessionStorage.removeItem("anis_jwt");
  showLogin();
  location.reload();
});

openAiBtn.addEventListener("click", () => {
  aiWidget.classList.remove("hidden");
  openAiBtn.classList.add("hidden");
});

closeAi.addEventListener("click", () => {
  aiWidget.classList.add("hidden");
  openAiBtn.classList.remove("hidden");
});

launchBtn.addEventListener("click", () => {
  aiWidget.classList.remove("hidden");
  openAiBtn.classList.add("hidden");
  widgetInput.focus();
});

checkBtn.addEventListener("click", () => {
  pollHealth();
});

window.addEventListener("load", async () => {
  const existingToken = getToken();
  if (existingToken) {
    showDashboard();
  } else {
    showLogin();
  }

  await pollHealth();
  setInterval(pollHealth, 30000);
});
