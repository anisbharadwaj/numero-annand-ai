// Global System Configurations
// IMPORTANT: Replace this address with your real live Render Web Service URL once deployed!
const API_BASE_URL = "https://protected-ethical-anis-ai.onrender.com"; 

let authToken = localStorage.getItem("anis_ai_token") || null;
let chatMemory = [];
let widgetMemory = [];

const authScreen = document.getElementById("auth-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const loginForm = document.getElementById("login-form");
const terminalLogs = document.getElementById("terminal-logs");

document.addEventListener("DOMContentLoaded", () => {
    if (authToken) {
        showDashboard();
    }
    setupWidgetEvents();
    setupDashboardEvents();
});

function showNotification(message, type = "blue") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast`;
    toast.style.borderLeftColor = type === "cyan" ? "#00f3ff" : type === "red" ? "#ff3333" : "#0066ff";
    toast.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.4s";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

function writeLog(text) {
    const line = document.createElement("div");
    line.className = "log-line";
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
}

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const captchaChecked = document.getElementById("captcha-check").checked;

    const btn = document.getElementById("login-submit-btn");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> RUNNING DECRYPTION CHECK...`;

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
            throw new Error(errorData.detail || "Authentication Failed.");
        }

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem("anis_ai_token", authToken);
        
        showNotification("Access Key Authorized. Unlocking Terminal.", "cyan");
        showDashboard();
    } catch (err) {
        showNotification(err.message, "red");
        writeLog(`[SECURITY ALERT] Denied entry attempt: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fas fa-unlock-alt"></i> INITIALIZE DECRYPTION`;
    }
});

function showDashboard() {
    authScreen.classList.add("hidden");
    dashboardScreen.classList.remove("hidden");
    writeLog("[SYSTEM] Administrative node mounted successfully.");
    runDiagnosticCheck();
}

async function runDiagnosticCheck() {
    writeLog("[DIAGNOSTIC] Checking structural API cluster connection state...");
    const startTime = performance.now();
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error("Health status non-200 endpoint.");
        
        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);
        
        document.getElementById("lbl-status").innerText = "SECURE / ONLINE";
        document.getElementById("lbl-status").className = "val text-cyan";
        document.getElementById("lbl-uptime").innerText = data.uptime;
        document.getElementById("lbl-latency").innerText = `${latency} ms`;
        
        writeLog(`[DIAGNOSTIC OK] Ping succeeded. Latency: ${latency}ms. AI Module Ready: ${data.ai_connected}`);
    } catch (err) {
        document.getElementById("lbl-status").innerText = "CRITICAL / DISCONNECTED";
        document.getElementById("lbl-status").className = "val text-red";
        writeLog(`[DIAGNOSTIC FAILED] Backend structural communication timeout.`);
        showNotification("Security perimeter connection warning.", "red");
    }
}

function setupDashboardEvents() {
    document.getElementById("btn-check").addEventListener("click", runDiagnosticCheck);
    document.getElementById("btn-launch").addEventListener("click", () => {
        writeLog("[SYSTEM] Flushing routing buffers and deploying virtual layers...");
        showNotification("All operational firewalls are armed and monitoring traffic.", "cyan");
    });

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
                showNotification("Session key expired. Re-authentication sequence forced.", "red");
                localStorage.removeItem("anis_ai_token");
                window.location.reload();
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Execution generation error.");
            }

            const data = await response.json();
            appendMessage("main-chat-output", data.response, "ai-msg");
            
            chatMemory.push({ role: "user", text: prompt });
            chatMemory.push({ role: "model", text: data.response });

        } catch (err) {
            loader.remove();
            appendMessage("main-chat-output", `Execution Interrupted: ${err.message}`, "ai-msg text-red");
        }
    });
}

function setupWidgetEvents() {
    const trigger = document.getElementById("widget-trigger");
    const panel = document.getElementById("widget-panel");
    const closeBtn = document.getElementById("widget-close-btn");
    const icon = document.getElementById("widget-icon-closed");

    trigger.addEventListener("click", () => {
        panel.classList.toggle("hidden");
        icon.className = panel.classList.contains("hidden") ? "fas fa-comment-slash" : "fas fa-comments text-cyan";
    });

    closeBtn.addEventListener("click", () => {
        panel.classList.add("hidden");
        icon.className = "fas fa-comment-slash";
    });

    document.getElementById("widget-chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const inputEl = document.getElementById("widget-input");
        const prompt = inputEl.value.trim();
        if(!prompt) return;

        appendMessage("widget-chat-output", prompt, "user-msg");
        inputEl.value = "";

        if(!authToken) {
            setTimeout(() => {
                appendMessage("widget-chat-output", "Access Warning: Authentication on main administrative dashboard panel is required to access AI functions.", "ai-msg");
            }, 500);
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
            if(!response.ok) throw new Error("Handshake drop.");

            const data = await response.json();
            appendMessage("widget-chat-output", data.response, "ai-msg");

            widgetMemory.push({ role: "user", text: prompt });
            widgetMemory.push({ role: "model", text: data.response });
        } catch(err) {
            loader.remove();
            appendMessage("widget-chat-output", "System data parsing failure.", "ai-msg");
        }
    });
}

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
    showNotification("Security Alert: Master root password overrides must be configured directly within the host service provider dashboard settings.", "cyan");
}
