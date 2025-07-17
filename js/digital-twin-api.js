// Digital Twin Health Dashboard API Service
class DigitalTwinAPI {
    constructor() {
        // Use configuration from digital-twin-config.js if available
        if (window.DIGITAL_TWIN_CONFIG) {
            this.baseURL = window.DIGITAL_TWIN_CONFIG.getAPIBaseURL();
            this.config = window.DIGITAL_TWIN_CONFIG;
        } else {
            // Fallback configuration
            this.baseURL = 'http://localhost:8000';
            this.config = {
                DASHBOARD: { CACHE_TIMEOUT: 5 * 60 * 1000, MAX_RETRIES: 3, RETRY_DELAY: 1000 },
                FEATURES: { MOCK_API: true }
            };
        }
        
        this.cache = new Map();
        
        // Log configuration for debugging
        console.log('🏥 Digital Twin API Service initialized:');
        console.log('Base URL:', this.baseURL);
        console.log('Mock API enabled:', this.config.FEATURES?.MOCK_API || false);
    }

    // Generic API request method with retry logic
    async makeRequest(url, options = {}) {
        const maxRetries = this.config.DASHBOARD?.MAX_RETRIES || 3;
        const retryDelay = this.config.DASHBOARD?.RETRY_DELAY || 1000;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    ...options
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return response;
            } catch (error) {
                console.warn(`API request attempt ${attempt} failed:`, error.message);
                
                if (attempt === maxRetries) {
                    throw error;
                }
                
                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
            }
        }
    }

    // Cache management
    getCachedData(key) {
        const cached = this.cache.get(key);
        const timeout = this.config.DASHBOARD?.CACHE_TIMEOUT || 5 * 60 * 1000;
        
        if (cached && (Date.now() - cached.timestamp) < timeout) {
            console.log(`📦 Cache hit for: ${key}`);
            return cached.data;
        }
        
        if (cached) {
            this.cache.delete(key);
        }
        return null;
    }

    setCachedData(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
        console.log(`💾 Cached data for: ${key}`);
    }

    // Health Data API methods
    async getRegionData(region) {
        const cacheKey = `region_${region}`;
        const cached = this.getCachedData(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            const url = `${this.baseURL}/api/health/region/${region}`;
            const response = await this.makeRequest(url);
            const data = await response.json();
            
            this.setCachedData(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`Failed to fetch region data for ${region}:`, error);
            throw new Error(`Unable to load health data for ${region}. Please try again.`);
        }
    }

    async getYearData(year) {
        const cacheKey = `year_${year}`;
        const cached = this.getCachedData(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            const url = `${this.baseURL}/api/health/history/${year}`;
            const response = await this.makeRequest(url);
            const data = await response.json();
            
            this.setCachedData(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`Failed to fetch year data for ${year}:`, error);
            throw new Error(`Unable to load health data for ${year}. Please try again.`);
        }
    }

    async searchHealthData(query) {
        if (!query || query.length < 2) {
            return [];
        }

        const cacheKey = `search_${query.toLowerCase()}`;
        const cached = this.getCachedData(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            const url = `${this.baseURL}/api/health/search?q=${encodeURIComponent(query)}`;
            const response = await this.makeRequest(url);
            const data = await response.json();
            
            this.setCachedData(cacheKey, data);
            return data;
        } catch (error) {
            console.error(`Search failed for query "${query}":`, error);
            return [];
        }
    }

    async exportHealthData(options = {}) {
        try {
            const url = `${this.baseURL}/api/health/export`;
            const response = await this.makeRequest(url, {
                method: 'POST',
                body: JSON.stringify({
                    format: 'pdf',
                    includeTimeline: true,
                    includeAllRegions: true,
                    ...options
                })
            });

            return await response.blob();
        } catch (error) {
            console.error('Export failed:', error);
            throw new Error('Unable to export health data. Please try again.');
        }
    }

    // AI Assistant API methods
    async chatWithAssistant(message) {
        try {
            const url = `${this.baseURL}/api/ai/chat`;
            const response = await this.makeRequest(url, {
                method: 'POST',
                body: JSON.stringify({ message })
            });

            return await response.json();
        } catch (error) {
            console.error('Chat request failed:', error);
            throw new Error('Unable to connect to AI assistant. Please try again.');
        }
    }

    async getHealthAnalysis(data) {
        try {
            const url = `${this.baseURL}/api/ai/analysis`;
            const response = await this.makeRequest(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });

            return await response.json();
        } catch (error) {
            console.error('Analysis request failed:', error);
            throw new Error('Unable to analyze health data. Please try again.');
        }
    }

    // Patient Data API methods
    async getPatientProfile() {
        const cacheKey = 'patient_profile';
        const cached = this.getCachedData(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            const url = `${this.baseURL}/api/patient/profile`;
            const response = await this.makeRequest(url);
            const data = await response.json();
            
            this.setCachedData(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Failed to fetch patient profile:', error);
            throw new Error('Unable to load patient profile. Please try again.');
        }
    }

    async getPatientTimeline() {
        const cacheKey = 'patient_timeline';
        const cached = this.getCachedData(cacheKey);
        
        if (cached) {
            return cached;
        }

        try {
            const url = `${this.baseURL}/api/patient/timeline`;
            const response = await this.makeRequest(url);
            const data = await response.json();
            
            this.setCachedData(cacheKey, data);
            return data;
        } catch (error) {
            console.error('Failed to fetch patient timeline:', error);
            throw new Error('Unable to load patient timeline. Please try again.');
        }
    }

    // Utility methods
    clearCache() {
        this.cache.clear();
        console.log('🧹 Cache cleared');
    }

    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }

    // Health check method
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Initialize API service
window.digitalTwinAPI = new DigitalTwinAPI();
