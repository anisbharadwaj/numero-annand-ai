const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

const loginView = document.getElementById('login-view');
const dashView = document.getElementById('dashboard-view');
const monitor = document.getElementById('health-monitor');
const loginBtn = document.getElementById('loginBtn');

let chatHistory = []; // Stores AI memory context

// 1. Backend Health Polling
async function checkBackend() {
    try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
            const data = await res.json();
            monitor.className = "status-box success";
            monitor.innerHTML = `<i class="fa-solid fa-server"></i> ONLINE (v${data.version}) | Uptime: ${data.uptime}s`;
            if(document.getElementById('dash-uptime')) {
                document.getElementById('dash-uptime').innerText = `${data.uptime}s`;
                document.getElementById('dash-ai').innerText = data.ai_connected ? "ONLINE" : "API KEY ERR";
            }
        } else throw new Error("Offline");
    } catch (e) {
        monitor.className = "status-box warning";
        monitor.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> WAKING SERVER...`;
    }
}
checkBackend();
setInterval(checkBackend, 30000);

// 2. Login Flow
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    loginBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> AUTHENTICATING...`;
    loginBtn.disabled = true;

    const formData = new URLSearchParams();
    formData.append("username", document.getElementById('username').value.trim());
    formData.append("password", document.getElementById('password').value);
    formData.append("captcha_verified", "true");

    try {
        const res = await fetch(`${API_BASE_URL}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);

        sessionStorage.setItem("anis_jwt", data.access_token);
        document.getElementById('dash-user').innerText = data.user;
        
        loginBtn.innerHTML = `<i class="fa-solid fa-check-double"></i> ACCESS GRANTED`;
        loginBtn.style.background = "var(--green)";
        
        setTimeout(() => {
            loginView.classList.add('hidden');
            dashView.classList.remove('hidden');
            document.getElementById('openAiBtn').classList.remove('hidden');
        }, 800);

    } catch (error) {
        monitor.className = "status-box error";
        monitor.innerHTML = `<i class="fa-solid fa-ban"></i> ${error.message}`;
        loginBtn.innerHTML = `<i class="fa-solid fa-terminal"></i> INITIATE CONNECTION`;
        loginBtn.disabled = false;
    }
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    sessionStorage.removeItem("anis_jwt");
    location.reload();
});

// 3. AI Chat System with Memory
const aiWidget = document.getElementById('ai-widget');
const openAiBtn = document.getElementById('openAiBtn');
const chatBox = document.getElementById('chatBox');
const aiInput = document.getElementById('aiInput');

openAiBtn.addEventListener('click', () => { aiWidget.classList.remove('hidden'); openAiBtn.classList.add('hidden'); });
document.getElementById('closeAi').addEventListener('click', () => { aiWidget.classList.add('hidden'); openAiBtn.classList.remove('hidden'); });

async function sendChat() {
    const text = aiInput.value.trim();
    if (!text) return;

    chatBox.innerHTML += `<div class="msg user">${text}</div>`;
    aiInput.value = '';
    
    const typingId = 'typing-' + Date.now();
    chatBox.innerHTML += `<div class="msg ai" id="${typingId}"><i class="fas fa-ellipsis fa-fade"></i></div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const token = sessionStorage.getItem("anis_jwt");
        const res = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ message: text, history: chatHistory })
        });

        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);

        // Update memory arrays
        chatHistory.push({ role: "user", content: text });
        chatHistory.push({ role: "model", content: data.reply });

        document.getElementById(typingId).innerHTML = marked.parse(data.reply);
    } catch (e) {
        document.getElementById(typingId).innerHTML = `<span style="color:var(--red)">System Error: ${e.message}</span>`;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById('sendAi').addEventListener('click', sendChat);
aiInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendChat(); });
