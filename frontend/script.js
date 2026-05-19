document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('username', document.getElementById('email').value);
    formData.append('password', document.getElementById('password').value);
    formData.append('captcha_verified', document.getElementById('captcha_verified').checked);

    const response = await fetch('https://protected-ethical-anis-ai-12.onrender.com/api/login', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    console.log(result);
    // Proceed to biometric verify screen based on result...
});
