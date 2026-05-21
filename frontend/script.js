// REPLACE THIS WITH YOUR RENDER URL
const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

const views = {
    login: document.getElementById('login-view'),
    bio: document.getElementById('biometric-view'),
    dash: document.getElementById('dashboard-view')
};

let userState = { token: null, url: null, bioEnabled: false, activePlan: false };
let chatHistory = [];

// 1. Backend Health Check Polling
async function checkBackend() {
    try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
            document.getElementById('health-monitor').className = "status-box success";
            document.getElementById('health-monitor').innerText = "SYSTEM ONLINE - AWAITING LOGIN";
            document.getElementById('loginBtn').disabled = false;
        } else throw new Error();
    } catch {
        document.getElementById('health-monitor').className = "status-box warning";
        document.getElementById('health-monitor').innerText = "WAKING SERVER... PLEASE WAIT";
        document.getElementById('loginBtn').disabled = true;
        setTimeout(checkBackend, 5000); // Poll every 5 seconds
    }
}
checkBackend();

// 2. Login Submit
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    btn.innerText = "AUTHENTICATING...";
    
    const formData = new URLSearchParams();
    formData.append("username", document.getElementById('username').value.trim());
    formData.append("password", document.getElementById('password').value);
    formData.append("human_check", document.getElementById('humanCheck').checked);

    try {
        const res = await fetch(`${API_BASE_URL}/api/login`, { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail);

        userState.token = "Bearer " + data.access_token;
        userState.url = document.getElementById('username').value.trim();
        userState.bioEnabled = data.biometric_enabled;
        userState.activePlan = data.membership_active;
        
        document.getElementById('dash-user').innerText = userState.url;
        updateMembershipUI(data.membership_tier, data.membership_active);
        
        views.login.classList.add('hidden');
        views.bio.classList.remove('hidden'); 
    } catch (err) {
        btn.innerText = "INITIATE CONNECTION";
        alert("Login Error: " + err.message);
    }
});

// 3. WebAuthn Biometric Verification
document.getElementById('authBiometricBtn').addEventListener('click', async () => {
    const status = document.getElementById('bio-status');
    status.innerText = "Prompting device biometrics (Fingerprint/FaceID)...";
    
    try {
        let credentialId = "";
        
        if (!userState.bioEnabled) {
            // Setup new Biometric
            const publicKey = {
                challenge: new Uint8Array(32),
                rp: { name: "Anis-AI-Shield" },
                user: { id: new Uint8Array(16), name: userState.url, displayName: userState.url },
                pubKeyCredParams: [{ type: "public-key", alg: -7 }],
                authenticatorSelection: { authenticatorAttachment: "platform", userVerification: "required" },
                timeout: 60000
            };
            const credential = await navigator.credentials.create({ publicKey });
            credentialId = btoa(String.fromCharCode(...new Uint8Array(credential.rawId)));
            
            const res = await fetch(`${API_BASE_URL}/api/biometrics/register`, {
                method: "POST", headers: { "Content-Type": "application/json", "Authorization": userState.token },
                body: JSON.stringify({ credential_id: credentialId })
            });
            const data = await res.json();
            userState.token = "Bearer " + data.access_token;
            
        } else {
            // Verify existing Biometric
            const publicKey = { challenge: new Uint8Array(32), timeout: 60000, userVerification: "required" };
            const credential = await navigator.credentials.get({ publicKey });
            credentialId = btoa(String.fromCharCode(...new Uint8Array(credential.rawId)));
            
            const res = await fetch(`${API_BASE_URL}/api/biometrics/verify`, {
                method: "POST", headers: { "Content-Type": "application/json", "Authorization": userState.token },
                body: JSON.stringify({ credential_id: credentialId })
            });
            if(!res.ok) throw new Error("Biometric Mismatch");
            const data = await res.json();
            userState.token = "Bearer " + data.access_token;
        }

        views.bio.classList.add('hidden');
        views.dash.classList.remove('hidden');
        checkAIStatus();
        
    } catch (err) {
        status.innerText = "Verification failed or cancelled by user. Try again.";
        console.error(err);
    }
});

// 4. Dashboard & Membership Logic
function updateMembershipUI(tier, isActive) {
    const memText = document.getElementById('dash-membership');
    const upgBtn = document.getElementById('upgradeBtn');
    
    if (isActive) {
        memText.innerText = `${tier} (ACTIVE)`;
        memText.className = "text-green";
        upgBtn.classList.add('hidden');
    } else {
        memText.innerText = "FREE (LIMITED)";
        memText.className = "text-purple";
        upgBtn.classList.remove('hidden');
    }
}

document.getElementById('upgradeBtn').addEventListener('click', () => {
    document.getElementById('qr-modal').classList.remove('hidden');
});
document.getElementById('closeQrBtn').addEventListener('click', () => {
    document.getElementById('qr-modal').classList.add('hidden');
});

let selectedPlan = "MONTHLY";
document.querySelectorAll('.plan-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.plan-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        selectedPlan = e.target.dataset.plan;
    });
});

document.getElementById('confirmPaymentBtn').addEventListener('click', async () => {
    const formData = new URLSearchParams();
    formData.append("plan", selectedPlan);
    
    try {
        const res = await fetch(`${API_BASE_URL}/api/membership/upgrade`, {
            method: "POST", headers: { "Authorization": userState.token }, body: formData
        });
        if(res.ok) {
            alert("Payment Verified. AI Core Unlocked.");
            document.getElementById('qr-modal').classList.add('hidden');
            updateMembershipUI(selectedPlan, true);
            userState.activePlan = true;
            checkAIStatus();
        }
    } catch (e) { alert("Verification Error. Please try again."); }
});

function checkAIStatus() {
    if(userState.activePlan) {
        document.getElementById('openAiBtn').classList.remove('hidden');
    }
}

// 5. Intelligent AI Core (Chat Logic)
const aiWidget = document.getElementById('ai-widget');
const chatBox = document.getElementById('chatBox');
const aiInput = document.getElementById('aiInput');

document.getElementById('openAiBtn').addEventListener('click', () => { aiWidget.classList.remove('hidden'); });
document.getElementById('closeAi').addEventListener('click', () => { aiWidget.classList.add('hidden'); });

async function sendAiMsg() {
    const msg = aiInput.value.trim();
    if(!msg) return;
    
    chatBox.innerHTML += `<div class="msg user">${msg}</div>`;
    aiInput.value = "";
    
    const typingId = "msg-" + Date.now();
    chatBox.innerHTML += `<div class="msg ai" id="${typingId}">Analyzing network context...</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const res = await fetch(`${API_BASE_URL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": userState.token },
            body: JSON.stringify({ message: msg, history: chatHistory })
        });
        
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail || "Server Error");
        
        chatHistory.push({ role: "user", content: msg });
        chatHistory.push({ role: "model", content: data.reply });
        
        document.getElementById(typingId).innerHTML = marked.parse(data.reply);
    } catch (err) {
        document.getElementById(typingId).innerText = `[CORE ERROR]: ${err.message}`;
        document.getElementById(typingId).style.color = "var(--red)";
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

document.getElementById('sendAi').addEventListener('click', sendAiMsg);
aiInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendAiMsg(); });
document.getElementById('logoutBtn').addEventListener('click', () => location.reload());
