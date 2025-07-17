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
        const submitBtn = document.getElementById('login-submit');

        this.setLoading(submitBtn, true);
        this.clearMessages();

        try {
            // Call the login service with the correct parameter format
            const response = await window.apiService.login(email, password);
            
            if (response.access_token) {
                // Store auth token
                window.apiService.setToken(response.access_token);
                
                // Get user profile with the token
                try {
                    const userProfile = await window.apiService.getProfile();
                    this.currentUser = userProfile;
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                } catch (profileError) {
                    console.warn('Could not fetch profile, using response data:', profileError);
                    this.currentUser = response.user || { email: email };
                    localStorage.setItem('currentUser', JSON.stringify(this.currentUser));
                }

                this.showSuccess('Login successful! Redirecting...');
                
                // Redirect to dashboard after short delay
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            } else {
                throw new Error(response.message || 'Login failed');
            }

        } catch (error) {
            console.error('Login error:', error);
            this.showError(error.message || 'Login failed. Please check your credentials.');
        } finally {
            this.setLoading(submitBtn, false);
        }
    }

    async handleSignup(e) {
        e.preventDefault();
        
        const firstName = document.getElementById('signup-firstname').value;
        const lastName = document.getElementById('signup-lastname').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm-password').value;
        const submitBtn = document.getElementById('signup-submit');

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
            console.error('Signup error:', error);
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
        const loginContainer = document.getElementById('login-container');
        const signupContainer = document.getElementById('signup-container');
        
        if (loginContainer && signupContainer) {
            loginContainer.classList.remove('hidden');
            signupContainer.classList.add('hidden');
        }
        this.clearMessages();
    }

    showSignupPage() {
        const loginContainer = document.getElementById('login-container');
        const signupContainer = document.getElementById('signup-container');
        
        if (loginContainer && signupContainer) {
            loginContainer.classList.add('hidden');
            signupContainer.classList.remove('hidden');
        }
        this.clearMessages();
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
        const loadingElement = button.querySelector('[id$="-loading"]');
        const textElement = button.querySelector('[id$="-text"]');
        
        if (loading) {
            button.disabled = true;
            if (loadingElement) loadingElement.classList.remove('hidden');
            if (textElement) textElement.classList.add('hidden');
        } else {
            button.disabled = false;
            if (loadingElement) loadingElement.classList.add('hidden');
            if (textElement) textElement.classList.remove('hidden');
        }
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showMessage(message, type) {
        const messageElement = document.getElementById('auth-message');
        const messageText = document.getElementById('auth-message-text');
        
        if (messageElement && messageText) {
            messageElement.className = `mt-4 p-4 rounded-lg ${
                type === 'error' 
                    ? 'bg-red-900 border border-red-700 text-red-300' 
                    : 'bg-green-900 border border-green-700 text-green-300'
            }`;
            messageText.textContent = message;
            messageElement.classList.remove('hidden');
            
            // Auto-hide success messages after 5 seconds
            if (type === 'success') {
                setTimeout(() => {
                    messageElement.classList.add('hidden');
                }, 5000);
            }
        }
    }

    clearMessages() {
        const messageElement = document.getElementById('auth-message');
        if (messageElement) {
            messageElement.classList.add('hidden');
        }
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
