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
let lastHealthCheckTime = null;
let lastHealthInterval = null;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function setToken(token) {
  sessionStorage.setItem("anis_jwt", token);
}

function getToken() {
  return sessionStorage.getItem("anis_jwt") || "";
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
  healthMonitor.className = isError ? "status-box warning" : "status-box success";
  healthMonitor.innerHTML = message;
}

function updateLastCheckedTimer() {
  if (!lastHealthCheckTime) return;

  const secondsAgo = Math.floor((Date.now() - lastHealthCheckTime) / 1000);
  const lastCheckedEl = document.getElementById("lastChecked");

  if (lastCheckedEl) {
    lastCheckedEl.innerHTML = `<i class="fa-regular fa-clock"></i> Last checked ${secondsAgo}s ago`;
  }
}

class ConnectionManager {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.maxRetries = 8;
    this.baseDelay = 700;
  }

  async pingReady(timeoutMs = 2500) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(`${this.baseUrl}/ready`, {
        method: "GET",
        mode: "cors",
        cache: "no-store",
        signal: controller.signal,
      });
      return res.ok;
    } catch {
      return false;
    } finally {
      clearTimeout(timer);
    }
  }

  async connect(onStatus) {
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      if (await this.pingReady()) {
        return true;
      }

      const delay = Math.min(this.baseDelay * Math.pow(2, attempt), 12000);
      if (onStatus) {
        onStatus(`Waking up Anis AI... (${attempt + 1}/${this.maxRetries})`);
      }
      await sleep(delay);
    }
    throw new Error("Core severed.");
  }

  async request(path, options = {}, config = {}) {
    const retries = config.retries ?? 5;
    const timeout = config.timeout ?? 12000;
    const onStatus = config.onStatus || null;

    let lastError = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeout);

      try {
        const response = await fetch(`${this.baseUrl}${path}`, {
          ...options,
          mode: "cors",
          cache: "no-store",
          credentials: options.credentials ?? "include",
          signal: controller.signal,
        });

        clearTimeout(timer);

        if ([502, 503, 504].includes(response.status)) {
          lastError = new Error(`Server waking up (${response.status})`);
        } else {
          return response;
        }
      } catch (error) {
        clearTimeout(timer);
        lastError = error;
      }

      if (attempt < retries) {
        const delay = Math.min(this.baseDelay * Math.pow(2, attempt), 12000);
        if (onStatus) {
          onStatus(`Connecting to Anis AI... (${attempt + 1}/${retries + 1})`);
        }
        await sleep(delay);
      }
    }

    throw lastError || new Error("Request failed");
  }
}

const connectionManager = new ConnectionManager(API_BASE_URL);

async function pollHealth() {
  try {
    const start = Date.now();

    const response = await connectionManager.request(
      "/health",
      { method: "GET" },
      {
        retries: 1,
        timeout: 3000,
      }
    );

    if (!response.ok) {
      throw new Error("Health check failed");
    }

    const data = await response.json();
    const ping = Date.now() - start;

    healthRetryCount = 0;
    lastHealthCheckTime = Date.now();

    if (lastHealthInterval) {
      clearInterval(lastHealthInterval);
    }
    lastHealthInterval = setInterval(updateLastCheckedTimer, 1000);

    showNotice(
      `<i class="fa-solid fa-circle-check"></i> SERVER ONLINE • ${ping}ms`,
      false
    );

    if (serverStatus) serverStatus.innerText = "ONLINE";
    if (aiStatus) aiStatus.innerText = data.ai_initialized ? "READY" : "STARTING";

    if (monitorBox) {
      monitorBox.innerHTML = `
        <strong>Status:</strong> ${data.status}<br>
        <strong>Version:</strong> ${data.version}<br>
        <strong>Uptime:</strong> ${data.uptime}s<br>
        <strong>AI Initialized:</strong> ${data.ai_initialized ? "YES" : "NO"}<br>
        <strong>AI Connected:</strong> ${data.ai_connected ? "YES" : "NO"}<br>
        <strong>Latency:</strong> ${ping}ms<br><br>
        <div id="lastChecked">
          <i class="fa-regular fa-clock"></i> Last checked 0s ago
        </div>
      `;
    }
  } catch (error) {
    healthRetryCount++;

    if (serverStatus) serverStatus.innerText = "OFFLINE";
    if (aiStatus) aiStatus.innerText = "STANDBY";

    showNotice(
      `<i class="fa-solid fa-triangle-exclamation"></i> WAKING UP ANIS AI...`,
      true
    );

    if (monitorBox) {
      monitorBox.innerHTML = `
        <strong>Status:</strong> WAKING UP<br>
        <strong>Retry Count:</strong> ${healthRetryCount}<br>
        <strong>Note:</strong> Retrying automatically...
      `;
    }
  }
}

function appendMessage(container, text, type) {
  const div = document.createElement("div");
  div.className = `msg ${type}`;
  div.innerHTML = text;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addTypingMessage(container) {
  const id = `typing-${Date.now()}`;
  const div = document.createElement("div");
  div.className = "msg ai";
  div.id = id;
  div.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Thinking...`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function parseSSEFrame(frame) {
  const lines = frame.split("\n");
  const dataLines = lines.filter((line) => line.startsWith("data:"));
  const raw = dataLines.map((line) => line.slice(5).trim()).join("\n");
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function streamChat(container, inputEl) {
  const message = inputEl.value.trim();
  if (!message) return;

  appendMessage(container, message, "user");
  inputEl.value = "";

  const typingId = addTypingMessage(container);
  const target = document.getElementById(typingId);

  const token = getToken();

  try {
    await connectionManager.connect((statusText) => {
      showNotice(statusText, true);
    });

    const response = await connectionManager.request(
      "/api/chat/stream",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({ message }),
      },
      {
        retries: 4,
        timeout: 15000,
        onStatus: (statusText) => {
          showNotice(statusText, true);
        },
      }
    );

    if (!response.ok || !response.body) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "AI request failed");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let fullText = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let frameEnd;
      while ((frameEnd = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, frameEnd).trim();
        buffer = buffer.slice(frameEnd + 2);

        if (!frame) continue;

        const payload = parseSSEFrame(frame);
        if (!payload) continue;

        if (payload.type === "chunk") {
          fullText += payload.text || "";
          if (target) {
            if (window.marked) {
              target.innerHTML = marked.parse(fullText);
            } else {
              target.innerHTML = fullText;
            }
          }
        }

        if (payload.type === "error") {
          if (target) {
            target.innerHTML = `<span style="color:var(--danger)">AI processing failed.</span>`;
          }
          return;
        }
      }
    }

    if (target && !fullText.trim()) {
      target.innerHTML = "No response returned.";
    }
  } catch (error) {
    console.error("AI stream error:", error);
    if (target) {
      target.innerHTML = `<span style="color:var(--danger)">Connection to AI Core severed.</span>`;
    }
  } finally {
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }
}

if (document.getElementById("loginForm")) {
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
      const response = await connectionManager.request(
        "/api/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: formData,
          credentials: "include",
        },
        {
          retries: 6,
          timeout: 12000,
          onStatus: (statusText) => {
            showNotice(statusText, true);
          },
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Authentication Failed.");
      }

      if (data.access_token) {
        setToken(data.access_token);
      }

      showNotice("Access Key Authorized. Unlocking Terminal.", false);

      setTimeout(() => {
        showDashboard();
        pollHealth();
      }, 600);
    } catch (error) {
      console.error("Login error:", error);
      showNotice(error.message || "Failed to fetch.", true);
    } finally {
      loginBtn.disabled = false;
      loginBtn.innerHTML = `<i class="fa-solid fa-power-off"></i> INITIATE CONNECTION`;
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    try {
      await connectionManager.request(
        "/api/logout",
        {
          method: "POST",
          credentials: "include",
        },
        { retries: 1, timeout: 5000 }
      );
    } catch {
      // ignore logout errors
    }

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

if (sendAi) {
  sendAi.addEventListener("click", () => {
    streamChat(chatBox, aiInput);
  });
}

if (sendWidgetAi) {
  sendWidgetAi.addEventListener("click", () => {
    streamChat(widgetChatBox, widgetInput);
  });
}

if (aiInput) {
  aiInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      streamChat(chatBox, aiInput);
    }
  });
}

if (widgetInput) {
  widgetInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      streamChat(widgetChatBox, widgetInput);
    }
  });
}

window.addEventListener("load", async () => {
  const token = getToken();

  if (token) {
    showDashboard();
  } else {
    showLogin();
  }

  showNotice(
    `<i class="fas fa-spinner fa-spin"></i> CONNECTING TO ANIS AI CORE...`,
    true
  );

  connectionManager.connect((statusText) => {
    showNotice(statusText, true);
  }).catch(() => {
    showNotice("Backend unavailable. Retrying automatically...", true);
  });

  await pollHealth();
  setInterval(pollHealth, 20000);
});
