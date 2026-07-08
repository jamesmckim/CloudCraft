// webui/src/controllers/authControllers.js
import Auth from '../services/authService.js';

export class AuthController {
    constructor(startAppCallback) {
        this.loginBtn = document.getElementById('login-btn');
        this.overlay = document.getElementById('login-overlay');

        this.startApp = startAppCallback;
    }

    async init() {
        if (window.location.search.includes("code=") && window.location.search.includes("state=")) {
            await Auth.handleCallback();
        }

        // 2. Check if the user is already logged in
        const user = await Auth.getUser();

        if (user) {
            console.log("Logged in as:", user.profile.preferred_username);
            this.startApp();
            this.bindLogout();
            return;
        }

        // 3. User is not logged in. Bind the Keycloak redirect to the login button.
        if (this.loginBtn) {
            this.loginBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                try {
                    await Auth.login();
                } catch (err) {
                    alert("Failed to reach identity provider.");
                }
            });
        }
    }

    bindLogout() {
        const btn = document.getElementById('logout-btn');

        if (!btn) return;

        btn.removeEventListener('click', this.handleLogout);
        btn.addEventListener('click', this.handleLogout);
    }

    handleLogout = () => {
        Auth.logout();
    }

    hideLogin() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
        }
    }
}