const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

const loginView = document.getElementById("login-view");
const dashView = document.getElementById("dashboard-view");
const healthMonitor = document.getElementById("health-monitor");
const loginBtn = document.getElementById("loginBtn");

const openAiBtn = document.getElementById("openAiBtn");
const aiWidget = document.getElementById("ai-widget");

let lastHealthCheck = 0;

/* =========================
   FAST HEALTH CHECK SYSTEM
========================= */

async function pollHealth() {
    const start = Date.now();

    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: "GET",
            cache: "no-store"
        });

        const ping = Date.now() - start;

        if (!response.ok) {
            throw new Error("Server Offline");
        }

        const data = await response.json();

        lastHealthCheck = Math.floor(Date.now() / 1000);

        healthMonitor.className = "status-box success";

        healthMonitor.innerHTML = `
            <div>
                <i class="fa-solid fa-circle-check"></i>
                SERVER ONLINE
            </div>

            <div style="margin-top:6px;font-size:12px;">
                Ping: ${ping}ms
            </div>

            <div style="margin-top:4px;font-size:11px;color:#9effc7;">
                Last checked just now
            </div>
        `;

        const aiStatus = document.getElementById("dash-ai-status");

        if (aiStatus) {
            aiStatus.innerText = data.ai_connected
                ? "CONNECTED"
                : "OFFLINE";
        }

    } catch (error) {

        healthMonitor.className = "status-box warning";

        healthMonitor.innerHTML = `
            <div>
                <i class="fa-solid fa-triangle-exclamation"></i>
                SERVER STARTING...
            </div>

            <div style="margin-top:6px;font-size:11px;">
                Render free servers may take 30-60 seconds.
            </div>
        `;
    }
}

pollHealth();

setInterval(() => {
    pollHealth();

    const info = healthMonitor.querySelector("div:last-child");

    if (info && lastHealthCheck !== 0) {

        const seconds =
            Math.floor(Date.now() / 1000) - lastHealthCheck;

        info.innerHTML = `Last checked ${seconds}s ago`;
    }

}, 5000);

/* =========================
   LOGIN SYSTEM
========================= */

document
    .getElementById("loginForm")
    .addEventListener("submit", async (e) => {

        e.preventDefault();

        const username =
            document.getElementById("username").value.trim();

        const password =
            document.getElementById("password").value;

        const humanCheck =
            document.getElementById("humanCheck").checked;

        if (!humanCheck) {

            healthMonitor.className = "status-box warning";

            healthMonitor.innerHTML = `
                <i class="fa-solid fa-shield"></i>
                Human verification required.
            `;

            return;
        }

        loginBtn.disabled = true;

        loginBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            VERIFYING...
        `;

        try {

            const formData = new URLSearchParams();

            formData.append("username", username);
            formData.append("password", password);
            formData.append("captcha_verified", "true");

            const response = await fetch(
                `${API_BASE_URL}/api/login`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/x-www-form-urlencoded"
                    },
                    body: formData
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Authentication Failed"
                );
            }

            sessionStorage.setItem(
                "anis_jwt",
                data.access_token
            );

            healthMonitor.className = "status-box success";

            healthMonitor.innerHTML = `
                <i class="fa-solid fa-circle-check"></i>
                ACCESS GRANTED
            `;

            loginBtn.innerHTML = `
                <i class="fa-solid fa-unlock"></i>
                CONNECTED
            `;

            setTimeout(() => {

                loginView.classList.add("hidden");

                dashView.classList.remove("hidden");

                openAiBtn.classList.remove("hidden");

            }, 1200);

        } catch (error) {

            healthMonitor.className = "status-box warning";

            healthMonitor.innerHTML = `
                <i class="fa-solid fa-circle-xmark"></i>
                ${error.message}
            `;

            loginBtn.disabled = false;

            loginBtn.innerHTML = `
                <i class="fa-solid fa-power-off"></i>
                INITIATE CONNECTION
            `;
        }
    });

/* =========================
   LOGOUT
========================= */

document
    .getElementById("logoutBtn")
    .addEventListener("click", () => {

        sessionStorage.removeItem("anis_jwt");

        location.reload();
    });

/* =========================
   AI WIDGET
========================= */

openAiBtn.addEventListener("click", () => {

    aiWidget.classList.remove("hidden");

    openAiBtn.classList.add("hidden");
});

document
    .getElementById("closeAi")
    .addEventListener("click", () => {

        aiWidget.classList.add("hidden");

        openAiBtn.classList.remove("hidden");
    });

const chatBox = document.getElementById("chatBox");
const aiInput = document.getElementById("aiInput");
const sendAi = document.getElementById("sendAi");

async function sendToAi() {

    const message = aiInput.value.trim();

    if (!message) return;

    chatBox.innerHTML += `
        <div class="msg user">
            ${message}
        </div>
    `;

    aiInput.value = "";

    const typingId = `typing-${Date.now()}`;

    chatBox.innerHTML += `
        <div class="msg ai" id="${typingId}">
            <i class="fas fa-spinner fa-spin"></i>
            Thinking...
        </div>
    `;

    chatBox.scrollTop = chatBox.scrollHeight;

    try {

        const token =
            sessionStorage.getItem("anis_jwt");

        const response = await fetch(
            `${API_BASE_URL}/api/chat`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message
                })
            }
        );

        const data = await response.json();

        document.getElementById(typingId).innerHTML =
            data.reply || "No AI response";

    } catch (error) {

        document.getElementById(typingId).innerHTML = `
            <span style="color:red;">
                AI connection failed.
            </span>
        `;
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}

sendAi.addEventListener("click", sendToAi);

aiInput.addEventListener("keypress", (e) => {

    if (e.key === "Enter") {
        sendToAi();
    }
});
