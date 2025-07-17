// Digital Twin Health Dashboard Configuration

window.DIGITAL_TWIN_CONFIG = {
    // Development mode - set to true for local development
    DEVELOPMENT_MODE: true,
    
    // Ngrok URLs - UPDATED WITH YOUR ACTUAL NGROK URLS (corrected mapping)
    NGROK_BACKEND_URL: 'https://lenient-sunny-grouse.ngrok-free.app',    // Backend service ngrok URL (port 8081)
    NGROK_AGENTS_URL: 'https://mackerel-liberal-loosely.ngrok-free.app',      // Agents service ngrok URL (port 8000)
    
    // Local URLs (fallback)
    LOCAL_BACKEND_URL: 'http://localhost:8081',
    LOCAL_AGENTS_URL: 'http://localhost:8000',
    
    // API endpoints configuration for Digital Twin Health Dashboard
    ENDPOINTS: {
        // Authentication endpoints
        AUTH: {
            LOGIN: '/auth/login',
            REGISTER: '/auth/signup',
            LOGOUT: '/auth/logout',
            ME: '/users/me',
            PROFILE: '/users/me'
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
        'shoulder', 'lungs', 'heart', 'liver', 'kidneys', 'stomach'
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
            REPORTS: '/api/reports',
            DOCUMENTS_UPLOAD: '/api/documents/upload',
            DOCUMENTS: '/api/documents'
        },
        
        // AI Agents endpoints - All endpoints now working!
        AGENTS: {
            // Core working endpoints
            CHAT: '/v1/chat/message',
            SYSTEM_STATUS: '/v1/system_info/system/status', 
            ANALYTICS_TRENDS: '/v1/analytics/analytics/trends',
            HEALTH_SCORE: '/v1/analytics/health/score',
            ANALYTICS_DASHBOARD: '/v1/analytics/analytics/dashboard',
            
            // FIXED! Medical Analysis endpoints (ChatResponse error resolved)
            SYMPTOM_ANALYSIS: '/v1/medical_analysis/symptoms/analyze',
            DIAGNOSTIC_SUGGESTIONS: '/v1/medical_analysis/diagnostic/suggestions',
            TREATMENT_RECOMMENDATIONS: '/v1/medical_analysis/treatment/recommendations',
            
            // FIXED! Knowledge Base endpoints (ChatResponse error resolved)
            KNOWLEDGE_SEARCH: '/v1/knowledge_base/knowledge/search',
            MEDICAL_INFORMATION: '/v1/knowledge_base/medical/information',
            DRUG_INTERACTIONS: '/v1/knowledge_base/drugs/interactions',
            
            // System info endpoints
            SYSTEM_METRICS: '/v1/system_info/metrics',
            DATABASE_STATUS: '/v1/system_info/database/status',
            API_INFO: '/v1/system_info/info',
            
            // Still broken (timeline service)
            TIMELINE: '/v1/timeline/timeline',  // Still has server error
            
            // Legacy endpoints (not in use)
            QUERY: '/api/agents/query',
            ANALYZE_DOCUMENT: '/api/agents/analyze-document',
            HEALTH_INSIGHTS: '/api/agents/health-insights'
        }
    },
    
    // Get the appropriate backend URL based on environment
    getBackendURL: function() {
        if (this.DEVELOPMENT_MODE && this.NGROK_BACKEND_URL !== 'https://your-backend-ngrok-url.ngrok.io') {
            return this.NGROK_BACKEND_URL;
        }
        return this.LOCAL_BACKEND_URL;
    },
    
    // Get the appropriate agents URL based on environment
    getAgentsURL: function() {
        // Use localhost for now since ngrok tunnel is down
        return this.LOCAL_AGENTS_URL;
        // if (this.DEVELOPMENT_MODE && this.NGROK_AGENTS_URL !== 'https://your-agents-ngrok-url.ngrok.io') {
        //     return this.NGROK_AGENTS_URL;
        // }
        // return this.LOCAL_AGENTS_URL;
    }
};

// Configuration validation
if (window.MEDITWIN_CONFIG.DEVELOPMENT_MODE) {
    console.log('🔧 MediTwin Configuration:');
    console.log('Backend URL:', window.MEDITWIN_CONFIG.getBackendURL());
    console.log('Agents URL:', window.MEDITWIN_CONFIG.getAgentsURL());
    
    if (window.MEDITWIN_CONFIG.NGROK_BACKEND_URL === 'https://your-backend-ngrok-url.ngrok.io') {
        console.warn('⚠️  Please update NGROK_BACKEND_URL in js/config.js with your actual ngrok URL');
    }
    
    if (window.MEDITWIN_CONFIG.NGROK_AGENTS_URL === 'https://your-agents-ngrok-url.ngrok.io') {
        console.warn('⚠️  Please update NGROK_AGENTS_URL in js/config.js with your actual ngrok URL');
    }
}
