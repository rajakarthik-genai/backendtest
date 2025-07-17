// Agent Service Testing Panel - Comprehensive Integration
class AgentServiceTester {
    constructor() {
        this.apiService = window.apiService;
        this.results = {};
        this.init();
    }

    init() {
        this.createTestingPanel();
        this.bindEvents();
    }

    createTestingPanel() {
        // Check if panel already exists
        if (document.getElementById('agent-testing-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'agent-testing-panel';
        panel.className = 'fixed top-4 left-4 w-96 bg-gray-800 rounded-xl shadow-2xl border border-gray-700 z-50 hidden';
        
        panel.innerHTML = `
            <div class="p-4 border-b border-gray-700">
                <div class="flex items-center justify-between">
                    <h3 class="text-lg font-semibold text-white">Agent Service Tester</h3>
                    <button id="close-agent-panel" class="text-gray-400 hover:text-white">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
            </div>
            
            <div class="p-4 max-h-96 overflow-y-auto">
                <div class="space-y-4">
                    <div class="bg-gray-700 rounded-lg p-3">
                        <h4 class="text-sm font-medium text-white mb-2">Chat Services</h4>
                        <div class="space-y-2">
                            <button id="test-chat" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Test AI Chat
                            </button>
                            <button id="test-expert-chat" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Test Expert Chat
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-3">
                        <h4 class="text-sm font-medium text-white mb-2">Medical Analysis</h4>
                        <div class="space-y-2">
                            <button id="test-symptoms" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Analyze Symptoms
                            </button>
                            <button id="test-diagnostic" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Get Diagnostic Suggestions
                            </button>
                            <button id="test-treatment" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Treatment Recommendations
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-3">
                        <h4 class="text-sm font-medium text-white mb-2">Knowledge Base</h4>
                        <div class="space-y-2">
                            <button id="test-knowledge-search" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Search Medical Knowledge
                            </button>
                            <button id="test-medical-info" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Get Medical Information
                            </button>
                            <button id="test-drug-interactions" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Check Drug Interactions
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-3">
                        <h4 class="text-sm font-medium text-white mb-2">Timeline & Analytics</h4>
                        <div class="space-y-2">
                            <button id="test-timeline" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Get Timeline Data
                            </button>
                            <button id="test-analytics" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Analytics Dashboard
                            </button>
                        </div>
                    </div>
                    
                    <div class="bg-gray-700 rounded-lg p-3">
                        <h4 class="text-sm font-medium text-white mb-2">System Info</h4>
                        <div class="space-y-2">
                            <button id="test-metrics" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Service Metrics
                            </button>
                            <button id="test-database" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                Database Status
                            </button>
                            <button id="test-api-info" class="w-full text-left px-3 py-2 text-sm bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors">
                                API Information
                            </button>
                        </div>
                    </div>
                </div>
                
                <div id="test-results" class="mt-4 p-3 bg-gray-900 rounded-lg hidden">
                    <h4 class="text-sm font-medium text-white mb-2">Test Results:</h4>
                    <pre id="test-results-content" class="text-xs text-green-400 whitespace-pre-wrap"></pre>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }

    bindEvents() {
        // Close panel
        document.getElementById('close-agent-panel').addEventListener('click', () => {
            this.hidePanel();
        });

        // Chat services
        document.getElementById('test-chat').addEventListener('click', () => {
            this.testChatService();
        });

        document.getElementById('test-expert-chat').addEventListener('click', () => {
            this.testExpertChat();
        });

        // Medical analysis
        document.getElementById('test-symptoms').addEventListener('click', () => {
            this.testSymptomAnalysis();
        });

        document.getElementById('test-diagnostic').addEventListener('click', () => {
            this.testDiagnosticSuggestions();
        });

        document.getElementById('test-treatment').addEventListener('click', () => {
            this.testTreatmentRecommendations();
        });

        // Knowledge base
        document.getElementById('test-knowledge-search').addEventListener('click', () => {
            this.testKnowledgeSearch();
        });

        document.getElementById('test-medical-info').addEventListener('click', () => {
            this.testMedicalInformation();
        });

        document.getElementById('test-drug-interactions').addEventListener('click', () => {
            this.testDrugInteractions();
        });

        // Timeline & Analytics
        document.getElementById('test-timeline').addEventListener('click', () => {
            this.testTimeline();
        });

        document.getElementById('test-analytics').addEventListener('click', () => {
            this.testAnalytics();
        });

        // System info
        document.getElementById('test-metrics').addEventListener('click', () => {
            this.testServiceMetrics();
        });

        document.getElementById('test-database').addEventListener('click', () => {
            this.testDatabaseStatus();
        });

        document.getElementById('test-api-info').addEventListener('click', () => {
            this.testAPIInfo();
        });
    }

    showPanel() {
        document.getElementById('agent-testing-panel').classList.remove('hidden');
    }

    hidePanel() {
        document.getElementById('agent-testing-panel').classList.add('hidden');
    }

    showResults(title, data) {
        const resultsDiv = document.getElementById('test-results');
        const resultsContent = document.getElementById('test-results-content');
        
        resultsDiv.classList.remove('hidden');
        resultsContent.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
    }

    // Test Methods
    async testChatService() {
        try {
            const response = await this.apiService.chatWithAgent("Hello, test message for AI chat");
            this.showResults('Chat Service Test', response);
        } catch (error) {
            this.showResults('Chat Service Error', error.message);
        }
    }

    async testExpertChat() {
        try {
            const response = await this.apiService.getExpertOpinion("What are the symptoms of diabetes?");
            this.showResults('Expert Chat Test', response);
        } catch (error) {
            this.showResults('Expert Chat Error', error.message);
        }
    }

    async testSymptomAnalysis() {
        try {
            const response = await this.apiService.analyzeSymptoms({
                symptoms: ["headache", "fever", "fatigue"],
                duration: "3 days",
                severity: "moderate"
            });
            this.showResults('Symptom Analysis Test', response);
        } catch (error) {
            this.showResults('Symptom Analysis Error', error.message);
        }
    }

    async testDiagnosticSuggestions() {
        try {
            const response = await this.apiService.getDiagnosticSuggestions({
                symptoms: ["chest pain", "shortness of breath"],
                medical_history: "hypertension"
            });
            this.showResults('Diagnostic Suggestions Test', response);
        } catch (error) {
            this.showResults('Diagnostic Suggestions Error', error.message);
        }
    }

    async testTreatmentRecommendations() {
        try {
            const response = await this.apiService.getTreatmentRecommendations({
                condition: "diabetes",
                symptoms: ["fatigue", "increased thirst"],
                severity: "moderate"
            });
            this.showResults('Treatment Recommendations Test', response);
        } catch (error) {
            this.showResults('Treatment Recommendations Error', error.message);
        }
    }

    async testKnowledgeSearch() {
        try {
            const response = await this.apiService.searchMedicalKnowledge("diabetes treatment");
            this.showResults('Knowledge Search Test', response);
        } catch (error) {
            this.showResults('Knowledge Search Error', error.message);
        }
    }

    async testMedicalInformation() {
        try {
            const response = await this.apiService.getMedicalInformation("hypertension");
            this.showResults('Medical Information Test', response);
        } catch (error) {
            this.showResults('Medical Information Error', error.message);
        }
    }

    async testDrugInteractions() {
        try {
            const response = await this.apiService.checkDrugInteractions(["aspirin", "warfarin"]);
            this.showResults('Drug Interactions Test', response);
        } catch (error) {
            this.showResults('Drug Interactions Error', error.message);
        }
    }

    async testTimeline() {
        try {
            const response = await this.apiService.getTimeline({
                limit: 10,
                start_date: "2024-01-01",
                end_date: "2024-12-31"
            });
            this.showResults('Timeline Test', response);
        } catch (error) {
            this.showResults('Timeline Error', error.message);
        }
    }

    async testAnalytics() {
        try {
            const response = await this.apiService.getAnalyticsDashboard();
            this.showResults('Analytics Dashboard Test', response);
        } catch (error) {
            this.showResults('Analytics Dashboard Error', error.message);
        }
    }

    async testServiceMetrics() {
        try {
            const response = await this.apiService.getServiceMetrics();
            this.showResults('Service Metrics Test', response);
        } catch (error) {
            this.showResults('Service Metrics Error', error.message);
        }
    }

    async testDatabaseStatus() {
        try {
            const response = await this.apiService.getDatabaseStatus();
            this.showResults('Database Status Test', response);
        } catch (error) {
            this.showResults('Database Status Error', error.message);
        }
    }

    async testAPIInfo() {
        try {
            const response = await this.apiService.getAPIInfo();
            this.showResults('API Information Test', response);
        } catch (error) {
            this.showResults('API Information Error', error.message);
        }
    }
}

// Initialize agent service tester
window.agentServiceTester = new AgentServiceTester();
