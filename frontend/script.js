const API_BASE_URL = "YOUR_RENDER_URL_HERE"; // REPLACE THIS

document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const captchaChecked = document.getElementById("captcha_verified").checked;
    const btn = document.querySelector(".btn-verify");

    btn.disabled = true;
    btn.innerHTML = "PROBING...";

    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    formData.append("captcha_verified", captchaChecked ? "true" : "false");

    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            alert("Access Key Authorized. Unlocking Terminal.");
            console.log("Success:", result);
        } else {
            alert("Error: " + (result.detail || "Authentication Failed."));
        }
    } catch (err) {
        alert("Connection Error: Check console for details.");
        console.error("Fetch Error:", err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = "PROBE AND VERIFY IDENTITY";
    }
});
