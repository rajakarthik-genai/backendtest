// API Configuration and Service Layer
class APIService {
    constructor() {
        // Use configuration from config.js if available, otherwise fallback to defaults
        if (window.MEDITWIN_CONFIG) {
            this.backendBaseURL = window.MEDITWIN_CONFIG.getBackendURL();
            this.agentsBaseURL = window.MEDITWIN_CONFIG.getAgentsURL();
        } else {
            // Updated with your actual running ngrok URLs (corrected mapping):
            this.backendBaseURL = 'https://lenient-sunny-grouse.ngrok-free.app'; // meditwin-backend for auth (port 8081)
            this.agentsBaseURL = 'https://mackerel-liberal-loosely.ngrok-free.app';  // meditwin-agents for AI services (port 8000)
        }
        
        this.token = localStorage.getItem('authToken');
        
        // Log configuration for debugging
        console.log('🔗 API Service initialized:');
        console.log('Backend URL:', this.backendBaseURL);
        console.log('Agents URL:', this.agentsBaseURL);
    }

    // Set authentication token
    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
    }

    // Clear authentication token
    clearToken() {
        this.token = null;
        localStorage.removeItem('authToken');
    }

    // Get headers with authentication
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (includeAuth && this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // Generic request method with ngrok compatibility
    async request(url, options = {}) {
        try {
            // Add ngrok-specific headers if using ngrok URLs
            const headers = {
                ...this.getHeaders(),
                ...options.headers
            };
            
            // Add ngrok bypass header if URL contains ngrok
            if (url.includes('ngrok') || url.includes('ngrok-free.app')) {
                headers['ngrok-skip-browser-warning'] = 'true';
            }
            
            const response = await fetch(url, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            console.error('URL:', url);
            console.error('Options:', options);
            throw error;
        }
    }

    // Authentication Services (meditwin-backend)
    async login(email, password) {
        return this.request(`${this.backendBaseURL}/auth/login`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify({ email, password })
        });
    }

    async signup(userData) {
        return this.request(`${this.backendBaseURL}/auth/signup`, {
            method: 'POST',
            headers: this.getHeaders(false),
            body: JSON.stringify(userData)
        });
    }

    async logout() {
        return this.request(`${this.backendBaseURL}/auth/logout`, {
            method: 'POST'
        });
    }

    async getCurrentUser() {
        return this.request(`${this.backendBaseURL}/auth/me`);
    }

    async updateProfile(userData) {
        return this.request(`${this.backendBaseURL}/auth/profile`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    }

    // Medical Data Services (meditwin-backend)
    async getHealthData() {
        return this.request(`${this.backendBaseURL}/api/health/data`);
    }

    async getMedicalHistory() {
        return this.request(`${this.backendBaseURL}/api/medical/history`);
    }

    async getReports() {
        return this.request(`${this.backendBaseURL}/api/reports`);
    }

    async uploadDocument(formData) {
        // Don't set Content-Type for FormData, let browser set it
        return fetch(`${this.backendBaseURL}/api/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        });
    }

    async getDocuments() {
        return this.request(`${this.backendBaseURL}/api/documents`);
    }

    async deleteDocument(documentId) {
        return this.request(`${this.backendBaseURL}/api/documents/${documentId}`, {
            method: 'DELETE'
        });
    }

    // AI Agent Services (meditwin-agents) - Updated with correct endpoints
    async chatWithAgent(message, sessionId = null) {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/chat/message`, {
                method: 'POST',
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });
        } catch (error) {
            console.error('Chat API Error:', error);
            throw new Error('Chat service is temporarily unavailable. Please try again later.');
        }
    }

    // System Status (Working)
    async getSystemStatus() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/system_info/system/status`);
        } catch (error) {
            console.error('System Status Error:', error);
            return { status: 'unknown', error: error.message };
        }
    }

    // Analytics Services (Working)
    async getHealthTrends(period = '30d') {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/analytics/analytics/trends?period=${period}`);
        } catch (error) {
            console.error('Health Trends Error:', error);
            throw new Error('Health analytics temporarily unavailable.');
        }
    }

    async getHealthScore() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/analytics/health/score`);
        } catch (error) {
            console.error('Health Score Error:', error);
            return { score: 0, category: 'Unknown', message: 'Health score calculation unavailable' };
        }
    }

    async getAnalyticsDashboard() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/analytics/analytics/dashboard`);
        } catch (error) {
            console.error('Analytics Dashboard Error:', error);
            return { overview: {}, message: 'Dashboard data temporarily unavailable' };
        }
    }

    // Medical Analysis Services (NOW WORKING - ChatResponse error fixed!)
    async analyzeSymptoms(symptomsData) {
        return await this.request(`${this.agentsBaseURL}/v1/medical_analysis/symptoms/analyze`, {
            method: 'POST',
            body: JSON.stringify({
                symptoms: symptomsData.symptoms || [],
                duration: symptomsData.duration || '',
                severity: symptomsData.severity || 'moderate',
                context: symptomsData.context || ''
            })
        });
    }

    async getDiagnosticSuggestions(symptomsData) {
        return await this.request(`${this.agentsBaseURL}/v1/medical_analysis/diagnostic/suggestions`, {
            method: 'POST',
            body: JSON.stringify({
                symptoms: symptomsData.symptoms || [],
                medical_history: symptomsData.medical_history || ''
            })
        });
    }

    async getTreatmentRecommendations(conditionData) {
        return await this.request(`${this.agentsBaseURL}/v1/medical_analysis/treatment/recommendations`, {
            method: 'POST',
            body: JSON.stringify({
                condition: conditionData.condition || '',
                symptoms: conditionData.symptoms || [],
                severity: conditionData.severity || 'moderate'
            })
        });
    }

    // Knowledge Base Services (NOW WORKING - ChatResponse error fixed!)
    async searchMedicalKnowledge(query) {
        return await this.request(`${this.agentsBaseURL}/v1/knowledge_base/knowledge/search?query=${encodeURIComponent(query)}`);
    }

    async getMedicalInformation(topic) {
        return await this.request(`${this.agentsBaseURL}/v1/knowledge_base/medical/information?topic=${encodeURIComponent(topic)}`);
    }

    async checkDrugInteractions(medications) {
        return await this.request(`${this.agentsBaseURL}/v1/knowledge_base/drugs/interactions`, {
            method: 'POST',
            body: JSON.stringify({ medications })
        });
    }

    // Timeline Services (Currently broken)
    async getTimeline(filters = {}) {
        try {
            const params = new URLSearchParams();
            if (filters.limit) params.append('limit', filters.limit);
            if (filters.start_date) params.append('start_date', filters.start_date);
            if (filters.end_date) params.append('end_date', filters.end_date);
            
            const queryString = params.toString() ? `?${params.toString()}` : '';
            return await this.request(`${this.agentsBaseURL}/v1/timeline/timeline${queryString}`);
        } catch (error) {
            console.error('Timeline Error:', error);
            return {
                error: true,
                message: 'Medical timeline temporarily unavailable.',
                events: [],
                userMessage: 'Your medical timeline is temporarily unavailable. Data will be restored soon.'
            };
        }
    }

    // System Information Services
    async getServiceMetrics() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/system_info/metrics`);
        } catch (error) {
            console.error('Service Metrics Error:', error);
            return { error: true, message: 'Service metrics unavailable' };
        }
    }

    async getDatabaseStatus() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/system_info/database/status`);
        } catch (error) {
            console.error('Database Status Error:', error);
            return { error: true, message: 'Database status unavailable' };
        }
    }

    async getAPIInfo() {
        try {
            return await this.request(`${this.agentsBaseURL}/v1/system_info/info`);
        } catch (error) {
            console.error('API Info Error:', error);
            return { error: true, message: 'API information unavailable' };
        }
    }

    // Helper method to get current user ID
    getCurrentUserId() {
        try {
            const user = JSON.parse(localStorage.getItem('currentUser'));
            return user?.id || null;
        } catch {
            return null;
        }
    }

    // Health check for services
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.backendBaseURL}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }

    async checkAgentsHealth() {
        try {
            const response = await fetch(`${this.agentsBaseURL}/health`);
            return response.ok;
        } catch {
            return false;
        }
    }
}

// Create global API service instance
window.apiService = new APIService();
