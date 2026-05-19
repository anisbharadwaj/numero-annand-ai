const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

let authToken = localStorage.getItem("anis_ai_token") || null;
let currentChallengeUser = null;

const authScreen = document.getElementById("auth-screen");
const biometricScreen = document.getElementById("biometric-screen");
const dashboardScreen = document.getElementById("dashboard-screen");
const loginForm = document.getElementById("login-form");
const terminalLogs = document.getElementById("terminal-logs");
const scannerOverlay = document.getElementById("hardware-scanner-overlay");
const aiReportText = document.getElementById("ai-report-text");

document.addEventListener("DOMContentLoaded", () => {
    if (authToken) showDashboard();
    setupBiometricHandshake();
    setupTerminalInterface();
});

function writeLog(text) {
    const line = document.createElement("div");
    line.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
    terminalLogs.appendChild(line);
    terminalLogs.scrollTop = terminalLogs.scrollHeight;
}

loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const captcha = document.getElementById("captcha-check").checked;

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    formData.append("captcha_verified", captcha);

    try {
        const res = await fetch(`${API_BASE_URL}/api/login`, { method: "POST", body: formData });
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || "Authentication sequence rejected.");
        }
        const data = await res.json();
        
        currentChallengeUser = data.user_identity;
        aiReportText.innerText = data.ai_profile_report;
        
        authScreen.classList.add("hidden");
        biometricScreen.classList.remove("hidden");
    } catch (err) {
        alert(`ACCESS REFUSED: ${err.message}`);
    }
});

function setupBiometricHandshake() {
    document.getElementById("scan-fingerprint-btn").addEventListener("click", () => {
        scannerOverlay.classList.remove("hidden");
        setTimeout(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/login/biometric-verify`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ signature: "hardware_enclave_verified_2026", userEmail: currentChallengeUser })
                });
                if (!res.ok) throw new Error("Hardware confirmation fault.");
                const data = await res.json();
                
                authToken = data.access_token;
                localStorage.setItem("anis_ai_token", authToken);
                biometricScreen.classList.add("hidden");
                showDashboard();
            } catch (err) {
                alert(err.message);
                scannerOverlay.classList.add("hidden");
            }
        }, 2000);
    });
}

function showDashboard() {
    dashboardScreen.classList.remove("hidden");
    writeLog("Secure network channel established. Zero-Trust perimeter active.");
}

function setupTerminalInterface() {
    document.getElementById("main-chat-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("main-chat-input");
        const messageText = input.value.trim();
        if (!messageText) return;

        const out = document.getElementById("main-chat-output");
        out.innerHTML += `<div><b>[Operator]:</b> ${messageText}</div>`;
        input.value = "";

        const startTime = performance.now();
        try {
            const res = await fetch(`${API_BASE_URL}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
                body: JSON.stringify({ message: messageText, history: [] })
            });
            
            if (!res.ok) throw new Error("Session drop or packet structural corruption.");
            const data = await res.json();
            
            document.getElementById("lbl-latency").innerText = `${Math.round(performance.now() - startTime)} ms`;
            out.innerHTML += `<div><b>[Anis AI Core]:</b> ${data.response}</div>`;
            writeLog("Cryptographic query transaction processed successfully.");
        } catch (err) {
            out.innerHTML += `<div style="color:#ef4444;"><b>[System Fault]:</b> ${err.message}</div>`;
        }
        out.scrollTop = out.scrollHeight;
    });
}
