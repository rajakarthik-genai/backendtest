// Digital Twin Health Dashboard Configuration

window.DIGITAL_TWIN_CONFIG = {
    // Development mode - set to true for local development
    DEVELOPMENT_MODE: true,
    
    // API Base URLs
    API_BASE_URL: 'http://localhost:8000',
    FRONTEND_URL: 'http://localhost:3000',
    
    // API endpoints configuration for Digital Twin Health Dashboard
    ENDPOINTS: {
        // Health data endpoints
        HEALTH: {
            REGION: '/api/health/region',        // GET /api/health/region/{region}
            HISTORY: '/api/health/history',      // GET /api/health/history/{year}
            TIMELINE: '/api/health/timeline',    // GET /api/health/timeline?region={region}
            SEARCH: '/api/health/search',        // GET /api/health/search?q={query}
            EXPORT: '/api/health/export',        // POST /api/health/export
            CHAT: '/api/health/chat',           // POST /api/health/chat
            EXPERT_OPINION: '/api/health/expert_opinion'  // POST /api/health/expert_opinion
        },
        
        // Patient data endpoints
        PATIENT: {
            PROFILE: '/api/patient/profile',
            TIMELINE: '/api/patient/timeline',
            CONDITIONS: '/api/patient/conditions'
        },
        
        // AI Assistant endpoints
        AI: {
            CHAT: '/api/ai/chat',
            ANALYSIS: '/api/ai/analysis',
            RECOMMENDATIONS: '/api/ai/recommendations'
        }
    },
    
    // Dashboard settings
    DASHBOARD: {
        CACHE_TIMEOUT: 5 * 60 * 1000,  // 5 minutes
        AUTO_REFRESH: 30 * 1000,       // 30 seconds
        MAX_RETRIES: 3,
        RETRY_DELAY: 1000              // 1 second
    },
    
    // Health regions configuration
    HEALTH_REGIONS: [
        'head', 'shoulder', 'lungs', 'heart', 'liver', 'kidneys', 'stomach'
    ],
    
    // Timeline years
    TIMELINE_YEARS: [2019, 2020, 2021, 2022, 2023, 2024],
    
    // Severity levels and colors
    SEVERITY_LEVELS: {
        'severe': { color: '#ef4444', bgColor: '#dc2626' },
        'moderate': { color: '#f59e0b', bgColor: '#d97706' },
        'mild': { color: '#22c55e', bgColor: '#059669' },
        'normal': { color: '#3b82f6', bgColor: '#2563eb' }
    },
    
    // Feature flags
    FEATURES: {
        MOCK_API: true,           // Enable mock API for testing
        EXPORT_PDF: true,         // Enable PDF export
        AI_ASSISTANT: true,       // Enable AI assistant
        REAL_TIME_UPDATES: false, // Enable real-time updates
        VOICE_COMMANDS: false     // Enable voice commands
    },
    
    // Get the appropriate API base URL
    getAPIBaseURL() {
        if (this.DEVELOPMENT_MODE) {
            return this.API_BASE_URL;
        }
        return this.API_BASE_URL;
    },
    
    // Get full endpoint URL
    getEndpoint(category, endpoint) {
        const baseURL = this.getAPIBaseURL();
        return `${baseURL}${this.ENDPOINTS[category][endpoint]}`;
    },
    
    // Check if feature is enabled
    isFeatureEnabled(feature) {
        return this.FEATURES[feature] || false;
    }
};
