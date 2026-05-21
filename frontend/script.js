const API_BASE_URL =
  "https://protected-ethical-anis-ai-12.onrender.com";

let lastCheckTime = Date.now();

const healthMonitor =
  document.getElementById("health-monitor");

const loginView =
  document.getElementById("login-view");

const dashView =
  document.getElementById("dashboard-view");

const loginBtn =
  document.getElementById("loginBtn");

const openAiBtn =
  document.getElementById("openAiBtn");

const aiWidget =
  document.getElementById("ai-widget");

const chatBox =
  document.getElementById("chatBox");

const aiInput =
  document.getElementById("aiInput");

const sendAi =
  document.getElementById("sendAi");

let retryCount = 0;

async function pollHealth() {

    try {

        const readyRes = await fetch(
            `${API_BASE_URL}/ready`,
            {
                cache: "no-store"
            }
        );

        if (!readyRes.ok) {
            throw new Error();
        }

        const healthRes = await fetch(
            `${API_BASE_URL}/health`,
            {
                cache: "no-store"
            }
        );

        const data = await healthRes.json();

        const secondsAgo =
          Math.floor(
            (Date.now() - lastCheckTime) / 1000
          );

        healthMonitor.className =
          "status-box success";

        healthMonitor.innerHTML = `
            <i class="fa-solid fa-circle-check"></i>
            SERVER ONLINE
            <br>
            AI:
            ${
              data.ai_initialized
                ? "CONNECTED"
                : "INITIALIZING"
            }
            <br>
            <small>
            Last checked ${secondsAgo}s ago
            </small>
        `;

        lastCheckTime = Date.now();

        retryCount = 0;

    } catch (e) {

        retryCount++;

        healthMonitor.className =
          "status-box warning";

        healthMonitor.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            WAKING SERVER...
            <br>
            <small>
            Retry ${retryCount}
            </small>
        `;
    }
}

pollHealth();

setInterval(pollHealth, 5000);

document
.getElementById("loginForm")
.addEventListener("submit", async (e) => {

    e.preventDefault();

    loginBtn.disabled = true;

    loginBtn.innerHTML =
      "CONNECTING...";

    const formData = new FormData();

    formData.append(
      "username",
      document
        .getElementById("username")
        .value
        .trim()
    );

    formData.append(
      "password",
      document
        .getElementById("password")
        .value
    );

    formData.append(
      "captcha_verified",
      document
        .getElementById("humanCheck")
        .checked
    );

    try {

        const res = await fetch(
            `${API_BASE_URL}/api/login`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await res.json();

        if (!res.ok) {

            throw new Error(
              data.detail
            );
        }

        sessionStorage.setItem(
          "anis_token",
          data.token
        );

        loginBtn.innerHTML =
          "CONNECTED";

        setTimeout(() => {

            loginView.classList.add(
              "hidden"
            );

            dashView.classList.remove(
              "hidden"
            );

            openAiBtn.classList.remove(
              "hidden"
            );

        }, 1000);

    } catch (err) {

        healthMonitor.className =
          "status-box warning";

        healthMonitor.innerHTML =
          err.message;

        loginBtn.disabled = false;

        loginBtn.innerHTML =
          "INITIATE CONNECTION";
    }
});

openAiBtn.addEventListener(
  "click",
  () => {

    aiWidget.classList.toggle(
      "hidden"
    );
});

document
.getElementById("closeAi")
.addEventListener(
  "click",
  () => {

    aiWidget.classList.add(
      "hidden"
    );
});

async function sendToAi() {

    const text =
      aiInput.value.trim();

    if (!text) return;

    chatBox.innerHTML += `
      <div class="msg user">
      ${text}
      </div>
    `;

    aiInput.value = "";

    const typingId =
      "typing-" + Date.now();

    chatBox.innerHTML += `
      <div
      class="msg ai"
      id="${typingId}">
      Thinking...
      </div>
    `;

    try {

        const token =
          sessionStorage.getItem(
            "anis_token"
          );

        const res = await fetch(
            `${API_BASE_URL}/api/chat`,
            {
                method: "POST",
                headers: {
                    "Content-Type":
                      "application/json",

                    "Authorization":
                      `Bearer ${token}`
                },

                body: JSON.stringify({
                    message: text
                })
            }
        );

        const data = await res.json();

        document.getElementById(
          typingId
        ).innerHTML =
          data.reply;

    } catch (e) {

        document.getElementById(
          typingId
        ).innerHTML =
          "Connection to AI Core severed.";
    }

    chatBox.scrollTop =
      chatBox.scrollHeight;
}

sendAi.addEventListener(
  "click",
  sendToAi
);

aiInput.addEventListener(
  "keypress",
  (e) => {

    if (e.key === "Enter") {
        sendToAi();
    }
});
