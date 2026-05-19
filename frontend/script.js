document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault(); // Stop page refresh
    
    const btn = document.querySelector('.btn-verify');
    btn.textContent = "PROBING..."; // Visual feedback
    btn.disabled = true;

    const formData = new FormData();
    formData.append('username', document.getElementById('email').value);
    formData.append('password', document.getElementById('password').value);
    formData.append('captcha_verified', document.getElementById('captcha_verified').checked);

    try {
        const response = await fetch('https://protected-ethical-anis-ai-12.onrender.com/api/login', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            alert("Success: " + JSON.stringify(result));
            // Redirect or show biometric screen here
        } else {
            alert("Error: " + (result.detail || "Authentication failed"));
        }
    } catch (err) {
        alert("Connection Error: Check console.");
        console.error(err);
    } finally {
        btn.textContent = "PROBE AND VERIFY IDENTITY";
        btn.disabled = false;
    }
});
