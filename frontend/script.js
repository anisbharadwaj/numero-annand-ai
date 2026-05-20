// MUST match your actual Render URL exactly, no trailing slash
const API_BASE_URL = "https://protected-ethical-anis-ai-12.onrender.com";

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const captchaChecked = document.getElementById('captcha_verified').checked;
    
    // Fix: Use FormData to match FastAPI Form(...) dependencies
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    formData.append("captcha_verified", captchaChecked ? "true" : "false");

    try {
        // Fix: Removed the broken space in the template literal
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            console.log("Auth Success:", data);
            // Store token securely and trigger UI transition to Dashboard
            sessionStorage.setItem("anis_token", data.access_token);
            transitionToDashboard(); 
        } else {
            alert(`Access Denied: ${data.detail}`);
        }
    } catch (error) {
        console.error("Network / CORS Error:", error);
        alert("Fatal Error: Could not connect to AI Core.");
    }
});
