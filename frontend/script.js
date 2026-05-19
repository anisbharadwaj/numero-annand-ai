// Global System Configurations
// Change this to your deployed Render URL (e.g., [https://your-app.onrender.com](https://your-app.onrender.com))
const API_BASE_URL = "[http://127.0.0.1:8000](http://127.0.0.1:8000)"; 

let authToken = localStorage.getItem("anis_ai_token") || null;
let chatMemory = [];
let widgetMemory = [];

// DOM Element Registry
const authScreen = document.getElementById("auth-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const loginForm = document.getElementById("login-form");
const terminalLogs = document.getElementById("terminal-logs");

// Boot / Authentication Checking Cycle
document.addEventListener("DOMContentLoaded", () => {
    if (authToken) {
        showDashboard();
    }
    setupWidgetEvents();
    setupDashboardEvents();
});

// Toast System Notification Manager
function showNotification(message, type = "blue") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast`;
    toast.style.borderLeftColor = type === "cyan" ? "#00f3ff" : type === "red" ? "#ff3838" : "#0077ff";
    toast.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.5s";
        setTimeout(() => toast.remove(), 500);
    }, 4000);
}

function writeLog(text) {
    const line = document.createElement("div");
    line.className = "log-line";
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
}

// Security Authentication Controller
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const captchaChecked = document.getElementById("captcha-check").checked;

    const btn = document.getElementById("login-submit-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> RUNNING COGNITIVE CHECK...`;

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    formData.append("captcha_verified", captchaChecked);

    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Authentication Vector Failure.");
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem("anis_ai_token", authToken);
        
        showNotification("Access Key Verified. Initializing Terminal.", "cyan");
        showDashboard();
    } catch (err) {
        showNotification(err.message, "red");
        writeLog(`[WARN] Access denied: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-unlock-alt"></i> INITIALIZE DECRYPTION`;
    }
});

function showDashboard() {
    authScreen.classList.add("hidden");
    dashboardScreen.classList.remove("hidden");
    writeLog("[SYSTEM] Admin Dashboard layer mounted successfully.");
    runDiagnosticCheck();
}

// Diagnostic Performance Checker Suite
async function runDiagnosticCheck() {
    writeLog("[DIAG] Sending handshake signal to backend...");
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error("Endpoint returned non-200 state.");
        
        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        
        document.getElementById("lbl-status").innerText = "SECURE / ONLINE";
        document.getElementById("lbl-status").className = "val text-cyan";
        document.getElementById("lbl-uptime").innerText = data.uptime;
        document.getElementById("lbl-latency").innerText = `${latency} ms`;
        
        writeLog(`[OK] Handshake verified. Latency: ${latency}ms. AI Core Status: ${data.ai_connected}`);
    } catch (err) {
        document.getElementById("lbl-status").innerText = "ERROR / DISCONNECTED";
        document.getElementById("lbl-status").className = "val text-red";
        writeLog(`[ERROR] Backend connection severed or failing.`);
        showNotification("Diagnostics check failed. Verification timeout.", "red");
    }
}

function setupDashboardEvents() {
    document.getElementById("btn-check").addEventListener("click", runDiagnosticCheck);
    document.getElementById("btn-launch").addEventListener("click", () => {
        writeLog("[SYSTEM] Re-initializing security firewalls...");
        showNotification("Firewall systems active. Network listening standard ports.", "cyan");
    });

    // Dashboard Intelligent Chat form handler
    document.getElementById("main-chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const inputEl = document.getElementById("main-chat-input");
        const prompt = inputEl.value.trim();
        if (!prompt) return;

        appendMessage("main-chat-output", prompt, "user-msg");
        inputEl.value = "";

        const loader = appendTypingIndicator("main-chat-output");

        try {
            const response = await fetch(`${API_BASE_URL}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({ message: prompt, history: chatMemory })
            });

            loader.remove();

            if (response.status === 401) {
                showNotification("Session keys invalid. Relog required.", "red");
                localStorage.removeItem("anis_ai_token");
                window.location.reload();
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Generation failure.");
            }

            const data = await response.json();
            appendMessage("main-chat-output", data.response, "ai-msg");
            
            // Save state context memory
            chatMemory.push({ role: "user", text: prompt });
            chatMemory.push({ role: "model", text: data.response });

        } catch (err) {
            loader.remove();
            appendMessage("main-chat-output", `Error executing logic: ${err.message}`, "ai-msg text-red");
        }
    });
}

// FLOATING WIDGET OPERATIONAL EMULATION
function setupWidgetEvents() {
    const trigger = document.getElementById("widget-trigger");
    const panel = document.getElementById("widget-panel");
    const closeBtn = document.getElementById("widget-close-btn");
    const icon = document.getElementById("widget-icon-closed");

    trigger.addEventListener("click", () => {
        panel.classList.toggle("hidden");
        if(panel.classList.contains("hidden")) {
            icon.className = "fas fa-comment-slash";
        } else {
            icon.className = "fas fa-comments text-cyan";
        }
    });

    closeBtn.addEventListener("click", () => {
        panel.classList.add("hidden");
        icon.className = "fas fa-comment-slash";
    });

    // Widget Form Submit Engine
    document.getElementById("widget-chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const inputEl = document.getElementById("widget-input");
        const prompt = inputEl.value.trim();
        if(!prompt) return;

        appendMessage("widget-chat-output", prompt, "user-msg");
        inputEl.value = "";

        // Guardrail: Enforce authentication even inside the floating ecosystem
        if(!authToken) {
            setTimeout(() => {
                appendMessage("widget-chat-output", "Access Alert: Core AI features require authenticated supervisor login on the main pane.", "ai-msg");
            }, 600);
            return;
        }

        const loader = appendTypingIndicator("widget-chat-output");

        try {
            const response = await fetch(`${API_BASE_URL}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${authToken}`
                },
                body: JSON.stringify({ message: prompt, history: widgetMemory })
            });

            loader.remove();
            if(!response.ok) throw new Error("Connection failed.");

            const data = await response.json();
            appendMessage("widget-chat-output", data.response, "ai-msg");

            widgetMemory.push({ role: "user", text: prompt });
            widgetMemory.push({ role: "model", text: data.response });
        } catch(err) {
            loader.remove();
            appendMessage("widget-chat-output", "System communication block.", "ai-msg");
        }
    });
}

// Helper DOM Element Renderers
 Boc
function appendMessage(containerId, text, className) {
    const container = document.getElementById(containerId);
    const msg = document.createElement("div");
    msg.className = className;
    msg.innerText = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator(containerId) {
    const container = document.getElementById(containerId);
    const loader = document.createElement("div");
    loader.className = "ai-msg";
    loader.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;
    container.appendChild(loader);
    container.scrollTop = container.scrollHeight;
    return loader;
}

function triggerForgotNotify(e) {
    e.preventDefault();
    showNotification("Security Protocol Override Required: Contact infrastructure architecture team to rotate secret hardware key variables.", "cyan");
}
