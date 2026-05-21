async function pollHealth() {
    const start = Date.now();

    healthMonitor.className = "status-box warning";
    healthMonitor.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        CONNECTING TO ANIS-AI-SHIELD CORE...
    `;

    try {
        const controller = new AbortController();

        // stop request after 15 seconds
        const timeout = setTimeout(() => controller.abort(), 15000);

        const res = await fetch(`${API_BASE_URL}/health`, {
            method: "GET",
            cache: "no-store",
            signal: controller.signal
        });

        clearTimeout(timeout);

        const ping = Date.now() - start;

        if (!res.ok) {
            throw new Error("Backend Offline");
        }

        const data = await res.json();

        healthMonitor.className = "status-box success";
        healthMonitor.innerHTML = `
            <i class="fa-solid fa-circle-check"></i>
            SERVER ONLINE • ${ping}ms
            <br>
            UPTIME: ${data.uptime}s
        `;

        // dashboard AI status
        const aiStatus = document.getElementById("dash-ai-status");

        if (aiStatus) {
            aiStatus.innerText = data.ai_connected
                ? "CONNECTED"
                : "AI OFFLINE";
        }

    } catch (err) {

        healthMonitor.className = "status-box warning";

        if (err.name === "AbortError") {
            healthMonitor.innerHTML = `
                <i class="fa-solid fa-cloud"></i>
                RENDER SERVER IS WAKING UP...
                <br>
                PLEASE WAIT 20-60 SECONDS
            `;
        } else {
            healthMonitor.innerHTML = `
                <i class="fa-solid fa-triangle-exclamation"></i>
                BACKEND OFFLINE OR FETCH FAILED
            `;
        }
    }
}

// Run immediately
pollHealth();

// Repeat every 20 sec
setInterval(pollHealth, 20000);
