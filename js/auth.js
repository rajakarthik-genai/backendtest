// Authentication Management
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Signup form
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignup(e));
        }

        // Switch between login and signup
        const showSignup = document.getElementById('show-signup');
        if (showSignup) {
            showSignup.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSignupPage();
            });
        }

        const showLogin = document.getElementById('show-login');
        if (showLogin) {
            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginPage();
            });
        }

        // Logout
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const submitBtn = e.target.querySelector('button[type="submit"]');

        this.setLoading(submitBtn, true);
        this.clearMessages();

        try {
            const response = await window.apiService.login(email, password);
            
            // Store auth token and user data
            window.apiService.setToken(response.token || response.access_token);
            this.currentUser = response.user;
            localStorage.setItem('currentUser', JSON.stringify(this.currentUser));

            this.showSuccess('Login successful! Redirecting...');
            
            // Redirect to dashboard after short delay
            setTimeout(() => {
                this.showDashboard();
            }, 1000);

        } catch (error) {
            this.showError(error.message || 'Login failed. Please try again.');
        } finally {
            this.setLoading(submitBtn, false);
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const username = document.getElementById('signup-username').value;
        const firstName = document.getElementById('signup-firstname').value;
        const lastName = document.getElementById('signup-lastname').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm').value;
        const submitBtn = e.target.querySelector('button[type="submit"]');

        this.setLoading(submitBtn, true);
        this.clearMessages();

        // Validate passwords match
        if (password !== confirmPassword) {
            this.showError('Passwords do not match.');
            this.setLoading(submitBtn, false);
            return;
        }

        try {
            const userData = {
                username,
                first_name: firstName,
                last_name: lastName,
                email,
                password
            };

            const response = await window.apiService.signup(userData);
            
            this.showSuccess('Account created successfully! Please login.');
            
            // Switch to login page after short delay
            setTimeout(() => {
                this.showLoginPage();
            }, 2000);

        } catch (error) {
            this.showError(error.message || 'Signup failed. Please try again.');
        } finally {
            this.setLoading(submitBtn, false);
        }
    }

    async handleLogout() {
        try {
            await window.apiService.logout();
        } catch (error) {
            console.warn('Logout API call failed:', error);
        } finally {
            // Clear local data regardless of API success
            window.apiService.clearToken();
            localStorage.removeItem('currentUser');
            this.currentUser = null;
            this.showLoginPage();
        }
    }

    checkAuthStatus() {
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('currentUser');

        if (token && userData) {
            try {
                this.currentUser = JSON.parse(userData);
                this.showDashboard();
                this.updateUserProfile();
            } catch (error) {
                console.error('Invalid user data in localStorage:', error);
                this.handleLogout();
            }
        } else {
            this.showLoginPage();
        }
    }

    showLoginPage() {
        this.hideAllPages();
        document.getElementById('login-page').classList.add('active');
        document.title = 'MediTwin - Login';
    }

    showSignupPage() {
        this.hideAllPages();
        document.getElementById('signup-page').classList.add('active');
        document.title = 'MediTwin - Sign Up';
    }

    showDashboard() {
        this.hideAllPages();
        document.getElementById('dashboard').style.display = 'flex';
        document.title = 'MediTwin - Dashboard';
        
        // Initialize dashboard if needed
        if (window.dashboardManager) {
            window.dashboardManager.init();
        }
    }

    hideAllPages() {
        const authContainers = document.querySelectorAll('.auth-container');
        authContainers.forEach(container => container.classList.remove('active'));
        
        const dashboard = document.getElementById('dashboard');
        if (dashboard) {
            dashboard.style.display = 'none';
        }
    }

    updateUserProfile() {
        if (this.currentUser) {
            const userNameElement = document.getElementById('user-name');
            const userAvatarElement = document.getElementById('user-avatar');
            
            if (userNameElement) {
                userNameElement.textContent = this.currentUser.name || this.currentUser.full_name || 'User';
            }
            
            if (userAvatarElement && this.currentUser.avatar) {
                userAvatarElement.src = this.currentUser.avatar;
            }

            // Update settings form if visible
            const settingsName = document.getElementById('settings-name');
            const settingsEmail = document.getElementById('settings-email');
            
            if (settingsName) {
                settingsName.value = this.currentUser.name || this.currentUser.full_name || '';
            }
            if (settingsEmail) {
                settingsEmail.value = this.currentUser.email || '';
            }
        }
    }

    setLoading(button, loading) {
        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        // Remove existing messages
        this.clearMessages();

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `${type}-message`;
        messageDiv.textContent = message;

        // Find active form and prepend message
        const activeForm = document.querySelector('.auth-container.active .auth-form');
        if (activeForm) {
            activeForm.insertBefore(messageDiv, activeForm.firstChild);
        }
    }

    clearMessages() {
        const messages = document.querySelectorAll('.error-message, .success-message');
        messages.forEach(msg => msg.remove());
    }

    getCurrentUser() {
        return this.currentUser;
    }

    isAuthenticated() {
        return !!this.currentUser && !!localStorage.getItem('authToken');
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
});
