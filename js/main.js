// Main Application Controller
class MediTwinApp {
    constructor() {
        this.isInitialized = false;
        this.init();
    }

    async init() {
        if (this.isInitialized) return;

        try {
            await this.waitForDOMReady();
            await this.initializeServices();
            this.bindGlobalEvents();
            this.setupErrorHandling();
            this.checkCompatibility();
            
            this.isInitialized = true;
            console.log('MediTwin application initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize MediTwin application:', error);
            this.showCriticalError('Application failed to initialize. Please refresh the page.');
        }
    }

    waitForDOMReady() {
        return new Promise((resolve) => {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', resolve);
            } else {
                resolve();
            }
        });
    }

    async initializeServices() {
        // Services are already initialized by their respective modules
        // Here we can add any cross-service initialization logic
        
        // Check if all required services are available
        const requiredServices = ['apiService', 'authManager'];
        for (const service of requiredServices) {
            if (!window[service]) {
                throw new Error(`Required service ${service} not found`);
            }
        }

        // Initialize optional services that depend on page context
        await this.initializeConditionalServices();
    }

    async initializeConditionalServices() {
        // Initialize services based on what's available in the DOM
        if (document.getElementById('chat-messages') && !window.chatManager) {
            // Chat manager will be initialized by its own module
        }

        if (document.getElementById('documents-list') && !window.documentManager) {
            // Document manager will be initialized by its own module
        }

        if (document.getElementById('dashboard') && !window.dashboardManager) {
            // Dashboard manager will be initialized by its own module
        }
    }

    bindGlobalEvents() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeyboard(e);
        });

        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {
            this.handleBrowserNavigation(e);
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            this.handleConnectionChange(true);
        });

        window.addEventListener('offline', () => {
            this.handleConnectionChange(false);
        });

        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });
    }

    handleGlobalKeyboard(e) {
        // Ctrl/Cmd + K: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Escape: Close modals
        if (e.key === 'Escape') {
            this.closeModals();
        }

        // Ctrl/Cmd + /: Show keyboard shortcuts
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            this.showKeyboardShortcuts();
        }
    }

    handleBrowserNavigation(e) {
        // Handle browser navigation for single-page app
        const path = window.location.pathname;
        const hash = window.location.hash;

        if (hash.startsWith('#page-')) {
            const pageName = hash.replace('#page-', '');
            if (window.dashboardManager) {
                window.dashboardManager.navigateToPage(pageName);
            }
        }
    }

    handleConnectionChange(isOnline) {
        const statusMessage = isOnline ? 
            'Connection restored' : 
            'Connection lost. Some features may not work.';
        
        const statusType = isOnline ? 'success' : 'warning';
        
        this.showNotification(statusMessage, statusType);

        // Update UI based on connection status
        document.body.classList.toggle('offline', !isOnline);
    }

    handleVisibilityChange() {
        if (document.hidden) {
            // Page is now hidden (user switched tabs)
            this.pauseUpdates();
        } else {
            // Page is now visible
            this.resumeUpdates();
        }
    }

    handleWindowResize() {
        // Trigger responsive updates
        this.updateResponsiveLayout();
    }

    pauseUpdates() {
        // Pause any real-time updates when tab is not visible
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }

    resumeUpdates() {
        // Resume updates when tab becomes visible
        this.startPeriodicUpdates();
    }

    startPeriodicUpdates() {
        // Check for updates every 30 seconds
        this.updateInterval = setInterval(() => {
            this.checkForUpdates();
        }, 30000);
    }

    async checkForUpdates() {
        // Check for new notifications, messages, etc.
        try {
            if (window.authManager?.isAuthenticated()) {
                // Check for any updates that need to be pulled
                await this.refreshUserData();
            }
        } catch (error) {
            console.warn('Failed to check for updates:', error);
        }
    }

    async refreshUserData() {
        // Refresh user data in background
        try {
            const user = await window.apiService.getCurrentUser();
            if (user && window.authManager) {
                window.authManager.currentUser = user;
                window.authManager.updateUserProfile();
            }
        } catch (error) {
            // Silently fail for background updates
            console.warn('Background user data refresh failed:', error);
        }
    }

    updateResponsiveLayout() {
        // Update layout based on screen size
        const isMobile = window.innerWidth < 768;
        document.body.classList.toggle('mobile-layout', isMobile);
        
        // Notify other components about layout change
        this.notifyLayoutChange(isMobile);
    }

    notifyLayoutChange(isMobile) {
        // Notify other managers about layout changes
        const layoutEvent = new CustomEvent('layoutChange', {
            detail: { isMobile }
        });
        document.dispatchEvent(layoutEvent);
    }

    closeModals() {
        // Close any open modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.remove();
        });
    }

    showKeyboardShortcuts() {
        const shortcuts = [
            { key: 'Ctrl + K', description: 'Focus search' },
            { key: 'Escape', description: 'Close modals' },
            { key: 'Ctrl + /', description: 'Show keyboard shortcuts' }
        ];

        const modal = document.createElement('div');
        modal.className = 'modal shortcuts-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-keyboard"></i> Keyboard Shortcuts</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="shortcuts-list">
                        ${shortcuts.map(shortcut => `
                            <div class="shortcut-item">
                                <kbd>${shortcut.key}</kbd>
                                <span>${shortcut.description}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('modal-close')) {
                modal.remove();
            }
        });
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.handleGlobalError(e.error);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.handleGlobalError(e.reason);
        });
    }

    handleGlobalError(error) {
        // Don't show error notifications for network errors during development
        if (error.message?.includes('fetch') || error.name === 'TypeError') {
            return;
        }

        // Show user-friendly error message
        this.showNotification(
            'An unexpected error occurred. Please try again.',
            'error'
        );
    }

    checkCompatibility() {
        const requiredFeatures = [
            'fetch',
            'localStorage',
            'addEventListener'
        ];

        const unsupportedFeatures = requiredFeatures.filter(feature => {
            return !(feature in window) && !(feature in document);
        });

        if (unsupportedFeatures.length > 0) {
            this.showCompatibilityWarning(unsupportedFeatures);
        }

        // Check for modern browser features
        this.checkModernFeatures();
    }

    checkModernFeatures() {
        const modernFeatures = {
            'Speech Recognition': 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
            'File Upload': 'FileReader' in window,
            'Drag and Drop': 'draggable' in document.createElement('div')
        };

        const unsupportedModern = Object.entries(modernFeatures)
            .filter(([name, supported]) => !supported)
            .map(([name]) => name);

        if (unsupportedModern.length > 0) {
            console.warn('Some modern features are not supported:', unsupportedModern);
        }
    }

    showCompatibilityWarning(unsupportedFeatures) {
        const warning = document.createElement('div');
        warning.className = 'compatibility-warning';
        warning.innerHTML = `
            <div class="warning-content">
                <h3><i class="fas fa-exclamation-triangle"></i> Browser Compatibility</h3>
                <p>Your browser doesn't support some required features:</p>
                <ul>
                    ${unsupportedFeatures.map(feature => `<li>${feature}</li>`).join('')}
                </ul>
                <p>Please update your browser for the best experience.</p>
                <button onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;

        warning.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 152, 0, 0.95);
            color: white;
            z-index: 10000;
            padding: 20px;
            text-align: center;
        `;

        document.body.appendChild(warning);
    }

    showCriticalError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.innerHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #ff4444;
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                z-index: 10000;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <h2><i class="fas fa-exclamation-circle"></i> Critical Error</h2>
                <p>${message}</p>
                <button onclick="location.reload()" style="
                    background: white;
                    color: #ff4444;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-top: 15px;
                ">Reload Page</button>
            </div>
        `;

        document.body.appendChild(errorDiv);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `app-notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196F3'
        };

        notification.innerHTML = `
            <i class="${icons[type]}"></i>
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 8px;
            max-width: 350px;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Auto-remove
        const timeout = setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, duration);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            clearTimeout(timeout);
            notification.remove();
        });
    }

    // Public API methods
    navigateTo(page) {
        if (window.dashboardManager) {
            window.dashboardManager.navigateToPage(page);
        }
    }

    openChat() {
        this.navigateTo('chat');
    }

    uploadDocument() {
        this.navigateTo('documents');
        // Trigger file upload
        setTimeout(() => {
            const uploadButton = document.getElementById('upload-document');
            if (uploadButton) {
                uploadButton.click();
            }
        }, 100);
    }

    // Utility methods for other components
    formatDate(date) {
        return new Date(date).toLocaleDateString();
    }

    formatTime(date) {
        return new Date(date).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDateTime(date) {
        return `${this.formatDate(date)} ${this.formatTime(date)}`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }

    .modal-content {
        background: white;
        border-radius: 12px;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    }

    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px;
        border-bottom: 1px solid #eee;
    }

    .modal-header h3 {
        margin: 0;
        color: #333;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .modal-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        transition: background-color 0.2s;
    }

    .modal-close:hover {
        background: #f5f5f5;
    }

    .modal-body {
        padding: 20px;
    }

    .modal-footer {
        padding: 20px;
        border-top: 1px solid #eee;
        text-align: right;
    }

    .shortcuts-list {
        display: grid;
        gap: 12px;
    }

    .shortcut-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
    }

    .shortcut-item kbd {
        background: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px 8px;
        font-family: monospace;
        font-size: 0.9em;
    }

    .offline .btn {
        opacity: 0.6;
        cursor: not-allowed;
    }

    .offline .btn:hover {
        transform: none;
    }

    @media (max-width: 768px) {
        .mobile-layout .sidebar {
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }

        .mobile-layout .sidebar.open {
            transform: translateX(0);
        }

        .mobile-layout .main-content {
            margin-left: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize the application
window.mediTwinApp = new MediTwinApp();
