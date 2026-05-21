const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

// ======================================================
// ELEMENTS
// ======================================================

const loginScreen = document.getElementById("login-screen");
const dashboardScreen = document.getElementById("dashboard-screen");

const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const humanCheck = document.getElementById("humanCheck");

const healthMonitor = document.getElementById("health-monitor");
const monitorBox = document.getElementById("monitorBox");

const serverStatus = document.getElementById("serverStatus");
const aiStatus = document.getElementById("aiStatus");

const launchBtn = document.getElementById("launchBtn");
const checkBtn = document.getElementById("checkBtn");
const logoutBtn = document.getElementById("logoutBtn");

const openAiBtn = document.getElementById("openAiBtn");
const aiWidget = document.getElementById("ai-widget");
const closeAi = document.getElementById("closeAi");

const chatBox = document.getElementById("chatBox");
const aiInput = document.getElementById("aiInput");
const sendAi = document.getElementById("sendAi");

// ======================================================
// GLOBALS
// ======================================================

let healthRetryCount = 0;
let lastHealthCheckTime = null;
let lastHealthInterval = null;

// ======================================================
// HELPERS
// ======================================================

function setToken(token) {
  sessionStorage.setItem("anis_jwt", token);
}

function getToken() {
  return sessionStorage.getItem("anis_jwt");
}

function removeToken() {
  sessionStorage.removeItem("anis_jwt");
}

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
  healthMonitor.className = isError
    ? "status-box warning"
    : "status-box success";

  healthMonitor.innerHTML = message;
}

function updateLastCheckedTimer() {
  if (!lastHealthCheckTime) return;

  const secondsAgo = Math.floor(
    (Date.now() - lastHealthCheckTime) / 1000
  );

  const lastCheckedEl = document.getElementById("lastChecked");

  if (lastCheckedEl) {
    lastCheckedEl.innerHTML =
      `<i class="fa-regular fa-clock"></i> Last checked ${secondsAgo}s ago`;
  }
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
  const controller = new AbortController();

  const timeout = setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      mode: "cors",
      cache: "no-store"
    });

    clearTimeout(timeout);

    return response;
  } catch (error) {
    clearTimeout(timeout);
    throw error;
  }
}

// ======================================================
// HEALTH CHECK
// ======================================================

async function pollHealth() {

  if (healthRetryCount === 0) {
    showNotice(
      `<i class="fas fa-spinner fa-spin"></i> CONNECTING TO SERVER...`,
      true
    );
  }

  try {

    const start = Date.now();

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/health`,
      {},
      8000
    );

    if (!response.ok) {
      throw new Error("Health check failed");
    }

    const data = await response.json();

    const latency = Date.now() - start;

    healthRetryCount = 0;

    lastHealthCheckTime = Date.now();

    if (lastHealthInterval) {
      clearInterval(lastHealthInterval);
    }

    lastHealthInterval = setInterval(updateLastCheckedTimer, 1000);

    showNotice(
      `<i class="fa-solid fa-circle-check"></i> SERVER ONLINE • ${latency}ms`,
      false
    );

    if (serverStatus) {
      serverStatus.innerText = "ONLINE";
    }

    if (aiStatus) {
      aiStatus.innerText = data.ai_connected
        ? "CONNECTED"
        : "OFFLINE";
    }

    if (monitorBox) {
      monitorBox.innerHTML = `
        <strong>Status:</strong> ${data.status}<br>
        <strong>Version:</strong> ${data.version}<br>
        <strong>Uptime:</strong> ${data.uptime}s<br>
        <strong>AI Connected:</strong> ${data.ai_connected ? "YES" : "NO"}<br>
        <strong>Latency:</strong> ${latency}ms<br><br>

        <div id="lastChecked">
          <i class="fa-regular fa-clock"></i> Last checked 0s ago
        </div>
      `;
    }

  } catch (error) {

    healthRetryCount++;

    if (serverStatus) {
      serverStatus.innerText = "OFFLINE";
    }

    if (aiStatus) {
      aiStatus.innerText = "STANDBY";
    }

    if (error.name === "AbortError") {

      showNotice(
        `<i class="fa-solid fa-cloud"></i> RENDER SERVER WAKING UP...`,
        true
      );

    } else {

      showNotice(
        `<i class="fa-solid fa-triangle-exclamation"></i> BACKEND OFFLINE OR FETCH FAILED`,
        true
      );
    }

    if (monitorBox) {
      monitorBox.innerHTML = `
        <strong>Status:</strong> OFFLINE<br>
        <strong>Retry Count:</strong> ${healthRetryCount}<br>
        <strong>Note:</strong> Retrying automatically...
      `;
    }

    console.error("Health Error:", error);
  }
}

// ======================================================
// LOGIN
// ======================================================

if (loginForm) {

  loginForm.addEventListener("submit", async (e) => {

    e.preventDefault();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!humanCheck.checked) {

      showNotice(
        "Please verify you are human first.",
        true
      );

      return;
    }

    if (!username || !password) {

      showNotice(
        "Render URL and password are required.",
        true
      );

      return;
    }

    loginBtn.disabled = true;

    loginBtn.innerHTML =
      `<i class="fas fa-spinner fa-spin"></i> CONNECTING...`;

    const formData = new URLSearchParams();

    formData.append("username", username);
    formData.append("password", password);
    formData.append("captcha_verified", "true");

    try {

      const response = await fetchWithTimeout(
        `${API_BASE_URL}/api/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded"
          },
          body: formData
        },
        12000
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed"
        );
      }

      setToken(data.access_token);

      showNotice(
        "ACCESS GRANTED • AI CORE ONLINE",
        false
      );

      loginBtn.innerHTML =
        `<i class="fa-solid fa-check"></i> CONNECTED`;

      setTimeout(() => {

        showDashboard();

        pollHealth();

      }, 700);

    } catch (error) {

      console.error("Login Error:", error);

      showNotice(
        error.message || "Failed to fetch",
        true
      );

      loginBtn.disabled = false;

      loginBtn.innerHTML =
        `<i class="fa-solid fa-power-off"></i> INITIATE CONNECTION`;
    }
  });
}

// ======================================================
// AI CHAT
// ======================================================

function appendMessage(message, type) {

  const div = document.createElement("div");

  div.className = `msg ${type}`;

  div.innerHTML = message;

  chatBox.appendChild(div);

  chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingMessage() {

  const id = `typing-${Date.now()}`;

  const div = document.createElement("div");

  div.className = "msg ai";

  div.id = id;

  div.innerHTML =
    `<i class="fas fa-ellipsis fa-fade"></i>`;

  chatBox.appendChild(div);

  chatBox.scrollTop = chatBox.scrollHeight;

  return id;
}

async function sendToAi() {

  const text = aiInput.value.trim();

  if (!text) return;

  appendMessage(text, "user");

  aiInput.value = "";

  const typingId = addTypingMessage();

  try {

    const token = getToken();

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/api/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          message: text
        })
      },
      20000
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.detail || "AI request failed"
      );
    }

    const reply =
      data.reply || "No response returned.";

    const target = document.getElementById(typingId);

    if (target) {

      if (window.marked) {
        target.innerHTML = marked.parse(reply);
      } else {
        target.innerHTML = reply;
      }
    }

  } catch (error) {

    console.error("AI Error:", error);

    const target = document.getElementById(typingId);

    if (target) {
      target.innerHTML =
        `<span style="color:red;">Connection to AI Core severed.</span>`;
    }
  }

  chatBox.scrollTop = chatBox.scrollHeight;
}

// ======================================================
// BUTTON EVENTS
// ======================================================

if (sendAi) {
  sendAi.addEventListener("click", sendToAi);
}

if (aiInput) {
  aiInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendToAi();
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {

    removeToken();

    location.reload();
  });
}

if (openAiBtn) {
  openAiBtn.addEventListener("click", () => {

    aiWidget.classList.remove("hidden");

    openAiBtn.classList.add("hidden");
  });
}

if (closeAi) {
  closeAi.addEventListener("click", () => {

    aiWidget.classList.add("hidden");

    openAiBtn.classList.remove("hidden");
  });
}

if (launchBtn) {
  launchBtn.addEventListener("click", () => {

    aiWidget.classList.remove("hidden");

    openAiBtn.classList.add("hidden");

    aiInput.focus();
  });
}

if (checkBtn) {
  checkBtn.addEventListener("click", () => {
    pollHealth();
  });
}

// ======================================================
// AUTO START
// ======================================================

window.addEventListener("load", async () => {

  const token = getToken();

  if (token) {
    showDashboard();
  } else {
    showLogin();
  }

  await pollHealth();

  setInterval(() => {
    pollHealth();
  }, 20000);
});
