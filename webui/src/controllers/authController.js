// webui/src/controllers/authControllers.js
import Auth from '../services/authService.js';

export class AuthController {
    constructor(startAppCallback) {
        this.loginForm = document.getElementById('login-form');
        this.overlay = document.getElementById('login-overlay');
		
		this.registerForm = document.getElementById('register-form');
        this.toggleText = document.getElementById('auth-toggle-text'); // "Don't have an account? Sign up"
		
        this.startApp = startAppCallback;
    }

    init() {
        if (Auth.getToken()) {
            this.startApp();
			this.bindLogout();
            return;
        }

        this.loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;

            try {
                await Auth.login(u, p);
                this.startApp();
				this.bindLogout();
            } catch (err) {
                alert("Unauthorized: Please check your credentials.");
            }
        });
		
		// Bind Registration Submission
        if (this.registerForm) {
            this.registerForm.addEventListener('submit', this.handleRegister.bind(this));
        }

        // Bind Toggle (Switch between Login/Register)
        if (this.toggleText) {
            this.toggleText.addEventListener('click', this.toggleAuthMode.bind(this));
        }
    }
	
	toggleAuthMode() {
        const isLoginVisible = this.loginForm.style.display !== 'none';
        
        if (isLoginVisible) {
            // Switch to Register
            this.loginForm.style.display = 'none';
            this.registerForm.style.display = 'block';
            this.toggleText.innerHTML = '<a href="#">Have an account? Login</a>';
        } else {
            // Switch to Login
            this.loginForm.style.display = 'block';
            this.registerForm.style.display = 'none';
            this.toggleText.innerHTML = '<a href="#">Need an account? Sign up</a>';
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const pass = document.getElementById('reg-password').value;
        const confirmPass = document.getElementById('reg-password-confirm').value;

        // Validation
        if (!this.validateEmail(email)) {
            alert("Please enter a valid email address.");
            return;
        }

        if (pass !== confirmPass) {
            alert("Passwords do not match!");
            return;
        }

        if (pass.length < 8) {
            alert("Password must be at least 8 characters long.");
            return;
        }

        try {
            await Auth.register(username, email, pass);
            alert("Account created successfully! Please login.");
            this.toggleAuthMode(); // Switch back to login view
        } catch (err) {
            alert(`Registration Error: ${err.message}`);
        }
    }

    validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(String(email).toLowerCase());
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
        this.overlay.style.display = 'none';
    }
}