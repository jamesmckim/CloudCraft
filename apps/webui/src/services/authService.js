// webui/src/services/authService.js

import { UserManager, WebStorageStateStore } from 'oidc-client-ts';

// OIDC Configuration for Keycloak
const oidcConfig = {
    // In production, this would be https://auth.craftcloud.com/realms/craftcloud
    authority: window.location.origin.includes('localhost')
        ? "http://localhost:8080/realms/craftcloud"
        : "https://auth.craftcloud.com/realms/craftcloud",
    client_id: "webui-client",
    redirect_uri: window.location.origin + "/", // Return to the main page after login
    post_logout_redirect_uri: window.location.origin + "/",
    response_type: "code",
    scope: "openid profile email",
    userStore: new WebStorageStateStore({ store: window.localStorage })
};

const userManager = new UserManager(oidcConfig);

const Auth = {
    async getUser() {
        return await userManager.getUser();
    },

    async getToken() {
        const user = await this.getUser();
        return user ? user.access_token : null;
    },

    async login() {
        await userManager.signinRedirect();
    },

    async logout() {
        await userManager.signoutRedirect();
    },

    async handleCallback() {
        try {
            // Processes the ?code=... URL parameters returning from Keycloak
            await userManager.signinRedirectCallback();

            // Clean up the URL so the user doesn't see the auth code
            window.history.replaceState({}, document.title, window.location.pathname);
            return true;
        } catch (err) {
            console.error("Error processing login callback", err);
            return false;
        }
    },

    // SECURE API CALLER
    async call(endpoint, options = {}) {
        const token = await this.getToken();

        // If no token, we can't make authorized calls
        if (!token) {
            console.warn("No token found, redirecting to login.");
            await this.login();
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