// webui/src/services/authService.js
const Auth = {
    // Storage Helpers
    saveToken(token) {
        localStorage.setItem('craftcloud_token', token);
    },

    getToken() {
        return localStorage.getItem('craftcloud_token');
    },

    logout() {
        localStorage.removeItem('craftcloud_token');
        // Refresh the page so the App Controller shows the login overlay again
        window.location.href = '/';
    },

    async login(username, password) {
        const params = new URLSearchParams();
		params.append('grant_type', 'password');
        params.append('username', username);
        params.append('password', password);

        const response = await fetch('/api/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
        });

        if (!response.ok) {
            throw new Error("Invalid username or password");
        }

        const data = await response.json();
        this.saveToken(data.access_token);
        return data;
    },
	
    async register(username, email, password) {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username: username,
                email: email,
                password: password 
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "Registration failed");
        }

        return await response.json();
    },

    // SECURE API CALLER
    async call(endpoint, options = {}) {
        const token = this.getToken();
		
		// If no token, we can't make authorized calls
		if (!token) {
			console.warn("No token found, redirecting to login.");
			window.location.href = '/';
			return;
		}
		
        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(endpoint, { ...options, headers });

        // Auto-logout if the token is expired/invalid
        if (response.status === 401) {
            this.logout();
        }

        return response;
    }
};

export default Auth;