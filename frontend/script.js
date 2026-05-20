// CONFIGURATION: Set your exact Render backend root directory here
const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

// Authentication System State Elements
let authToken = null;
let chatHistory = [];
let widgetHistory = [];

const authScreen = document.getElementById("auth-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const loginForm = document.getElementById("login-form");
const loginBtn = document.getElementById("login-submit-btn");

// --- 1. HANDLING THE SECURE ENTRY LOGIN GATEWAY ---
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const captchaChecked = document.getElementById("captcha_verified").checked;

    // Visual feedback execution update
    loginBtn.disabled = true;
    loginBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> RUNNING DECRYPTION CHECK...`;

    // Package as standard urlencoded fields to match Python backend validation definitions
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    formData.append("captcha_verified", captchaChecked ? "true" : "false");

    try {
        // FIXED URL CONCATENATION: No stray padding spaces allowed here
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Access mapping verification failure.");
        }

        // Simulating the stage-2 bypass to launch cleanly into 'Ask AI' dashboard as requested
        if (data.requires_biometrics) {
            console.log("Stage 1 Pass. Challenge: ", data.biometric_challenge);
            
            // Execute automated backdrop challenge handshake confirmation instantly to clear gateway
            const bioData = {
                signature: data.biometric_challenge,
                userEmail: data.user_identity
            };

            const bioResponse = await fetch(`${API_BASE_URL}/api/login/biometric-verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(bioData)
            });

            const bioResult = await bioResponse.json();

            if (!bioResponse.ok) {
                throw new Error(bioResult.detail || "Biometric validation structure failed.");
            }

            authToken = bioResult.access_token;
            sessionStorage.setItem("anis_token", authToken);
            
            // Trigger instant structural transition to direct AI dashboard access
            showNotification("Terminal Access Key Authorized.", "cyan");
            launchDashboard();
        }
    } catch (err) {
        showNotification(err.message, "red");
        console.error("[GATEWAY FAILURE]", err);
    } finally {
        loginBtn.disabled = false;
        loginBtn.innerHTML = `<i class="fas fa-unlock-alt"></i> INITIALIZE DECRYPTION`;
    }
});

function launchDashboard() {
    authScreen.classList.add("hidden");
    dashboardScreen.classList.remove("hidden");
    executeHealthCheck(); // Auto run diagnostics when dashboard opens
}

// --- 2. INTEGRATING INTELLIGENT AI SYSTEM ASSISTANT ---
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatTerminal = document.getElementById("chat-terminal");

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const queryText = chatInput.value.trim();
    if (!queryText) return;

    // Append operator query to display viewport array
    appendMessage(chatTerminal, "Operator", queryText);
    chatInput.value = "";

    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: queryText,
                history: chatHistory
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Neural mapping processing disconnect.");
        }

        // Render response data down to text layout interface
        appendMessage(chatTerminal, "Anis-AI", data.response);
        
        // Push interactions into session context logs array to avoid repeating questions
        chatHistory.push({ role: "user", text: queryText });
        chatHistory.push({ role: "model", text: data.response });

    } catch (err) {
        appendMessage(chatTerminal, "ERROR", err.message);
    }
});

// --- 3. SYSTEM HEALTH DIAGNOSTICS CONTROL ---
const checkHealthBtn = document.getElementById("check-health-btn");
const healthDisplay = document.getElementById("health-status-display");

async function executeHealthCheck() {
    healthDisplay.textContent = "Querying core status...";
    healthDisplay.className = "status-indicator processing";
    
    try {
        const res = await fetch(`${API_BASE_URL}/health`);
        const stats = await res.json();
        
        if (res.ok && stats.status === "ok") {
            healthDisplay.textContent = `SYS: OPERATIONAL | Uptime: ${stats.uptime}s | AI: ${stats.ai_connected ? 'LINKED' : 'ERR'}`;
            healthDisplay.className = "status-indicator online";
        } else {
            healthDisplay.textContent = "SYS: COLD_FAULT";
            healthDisplay.className = "status-indicator offline";
        }
    } catch {
        healthDisplay.textContent = "SYS: NET_DISCONNECT";
        healthDisplay.className = "status-indicator offline";
    }
}
checkHealthBtn.addEventListener("click", executeHealthCheck);

// --- 4. FLOATING ASSISTANT WIDGET HANDLING ---
const widgetBtn = document.getElementById("anis-widget-button");
const widgetWindow = document.getElementById("anis-widget-window");
const closeWidgetBtn = document.getElementById("close-widget-btn");
const widgetForm = document.getElementById("widget-chat-form");
const widgetInput = document.getElementById("widget-input");
const widgetLog = document.getElementById("widget-chat-log");

widgetBtn.addEventListener("click", () => widgetWindow.classList.toggle("hidden"));
closeWidgetBtn.addEventListener("click", () => widgetWindow.classList.add("hidden"));

widgetForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const txt = widgetInput.value.trim();
    if (!txt) return;

    appendMessage(widgetLog, "User", txt);
    widgetInput.value = "";

    try {
        // Widgets hit the open health path or open assistant context logic directly
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": authToken ? `Bearer ${authToken}` : "" 
            },
            body: JSON.stringify({ message: txt, history: widgetHistory })
        });
        const data = await response.json();
        
        if(!response.ok) throw new Error(data.detail || "Authentication Required for AI access.");
        
        appendMessage(widgetLog, "Anis-AI", data.response);
        widgetHistory.push({ role: "user", text: txt });
        widgetHistory.push({ role: "model", text: data.response });
    } catch(err) {
        appendMessage(widgetLog, "ALERT", err.message);
    }
});

// --- HELPER UTILITY LOGIC COMPONENTS ---
function appendMessage(targetLog, sender, text) {
    const msg = document.createElement("div");
    msg.className = `chat-bubble ${sender.toLowerCase()}`;
    msg.innerHTML = `<strong>[${sender}]:</strong> <span>${text}</span>`;
    targetLog.appendChild(msg);
    targetLog.scrollTop = targetLog.scrollHeight; // Auto scrolls text
}

function showNotification(text, toneColor) {
    const alertBox = document.createElement("div");
    alertBox.style.position = "fixed";
    alertBox.style.top = "20px";
    alertBox.style.left = "50%";
    alertBox.style.transform = "translateX(-50%)";
    alertBox.style.background = "#0a0a0f";
    alertBox.style.color = toneColor === "cyan" ? "#00f3ff" : "#ff0055";
    alertBox.style.border = `1px solid ${toneColor === "cyan" ? '#00f3ff' : '#ff0055'}`;
    alertBox.style.padding = "12px 24px";
    alertBox.style.fontFamily = "monospace";
    alertBox.style.zIndex = "99999";
    alertBox.textContent = `[NOTIFICATION]: ${text}`;
    document.body.appendChild(alertBox);
    setTimeout(() => alertBox.remove(), 4000);
}
