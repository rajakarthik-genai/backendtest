// Dashboard Management
class DashboardManager {
    constructor() {
        this.currentPage = 'dashboard';
        this.healthData = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadHealthData();
        this.checkServiceHealth();
    }

    bindEvents() {
        // Sidebar navigation
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.addEventListener('click', (e) => {
                const page = item.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Search functionality
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }

        // Health indicators
        const healthIndicators = document.querySelectorAll('.health-indicator');
        healthIndicators.forEach(indicator => {
            indicator.addEventListener('click', (e) => {
                this.showOrganDetails(indicator.dataset.organ);
            });
        });

        // Voice assistant
        const voiceBtn = document.querySelector('.voice-btn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', () => {
                this.startVoiceRecognition();
            });
        }

        // Year selector
        const yearSpans = document.querySelectorAll('.year');
        yearSpans.forEach(year => {
            year.addEventListener('click', (e) => {
                this.selectYear(e.target.textContent);
            });
        });
    }

    navigateToPage(pageId) {
        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${pageId}"]`).classList.add('active');

        // Show corresponding page
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(`${pageId}-page`).classList.add('active');

        this.currentPage = pageId;

        // Load page-specific data
        this.loadPageData(pageId);
    }

    async loadPageData(pageId) {
        switch (pageId) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'timeline':
                await this.loadTimelineData();
                break;
            case 'reports':
                await this.loadReportsData();
                break;
            case 'analysis':
                await this.loadAnalysisData();
                break;
            case 'documents':
                await this.loadDocumentsData();
                break;
            case 'settings':
                this.loadSettingsData();
                break;
        }
    }

    async loadHealthData() {
        try {
            const data = await window.apiService.getHealthData();
            this.healthData = data;
            this.updateHealthDisplay();
        } catch (error) {
            console.error('Failed to load health data:', error);
            this.showMockHealthData();
        }
    }

    updateHealthDisplay() {
        if (!this.healthData) return;

        // Update health indicators
        this.updateHealthIndicators();
        
        // Update conditions list
        this.updateConditionsList();
        
        // Update summary stats
        this.updateSummaryStats();
    }

    updateHealthIndicators() {
        const indicators = {
            shoulder: '#ff4444', // Red for severe
            lungs: '#ff8800',    // Orange for moderate
            liver: '#44ff44',    // Green for good
            kidneys: '#4488ff'   // Blue for monitored
        };

        Object.entries(indicators).forEach(([organ, color]) => {
            const indicator = document.querySelector(`[data-organ="${organ}"]`);
            if (indicator) {
                indicator.style.fill = color;
            }
        });
    }

    updateConditionsList() {
        // This would be populated with real data from the API
        const mockConditions = [
            {
                id: 1,
                name: 'Migraine - Severe Head Pain',
                severity: 'severe',
                symptoms: ['Severe headache', 'Throbbing pain', 'Nausea', 'Light sensitivity'],
                icon: 'fas fa-head-side-virus'
            }
        ];

        // Update conditions display
        console.log('Updating conditions:', mockConditions);
    }

    updateSummaryStats() {
        // Update the data summary section with real data
        const summarySection = document.querySelector('.data-summary');
        if (summarySection && this.healthData) {
            // Update with real health data
        }
    }

    showMockHealthData() {
        // Show sample data when API is not available
        console.log('Showing mock health data for development');
    }

    async loadDashboardData() {
        try {
            // Load health insights from AI agents
            const insights = await window.apiService.getHealthInsights();
            this.displayHealthInsights(insights);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    async loadTimelineData() {
        try {
            const history = await window.apiService.getMedicalHistory();
            this.displayTimeline(history);
        } catch (error) {
            console.error('Failed to load timeline data:', error);
            this.showMockTimeline();
        }
    }

    async loadReportsData() {
        try {
            const reports = await window.apiService.getReports();
            this.displayReports(reports);
        } catch (error) {
            console.error('Failed to load reports data:', error);
            this.showMockReports();
        }
    }

    async loadAnalysisData() {
        // Load and display health analysis charts
        this.initializeHealthChart();
    }

    async loadDocumentsData() {
        // Documents are handled by DocumentManager
        if (window.documentManager) {
            window.documentManager.loadDocuments();
        }
    }

    loadSettingsData() {
        // Settings data is loaded by AuthManager
        if (window.authManager) {
            window.authManager.updateUserProfile();
        }
    }

    displayHealthInsights(insights) {
        // Display AI-generated health insights
        console.log('Health insights:', insights);
    }

    displayTimeline(history) {
        const timelineContainer = document.querySelector('.timeline-container');
        if (!timelineContainer || !history) return;

        timelineContainer.innerHTML = '';
        
        history.forEach(item => {
            const timelineItem = document.createElement('div');
            timelineItem.className = 'timeline-item';
            timelineItem.innerHTML = `
                <div class="timeline-date">${new Date(item.date).toLocaleDateString()}</div>
                <div class="timeline-content">
                    <h4>${item.title}</h4>
                    <p>${item.description}</p>
                </div>
            `;
            timelineContainer.appendChild(timelineItem);
        });
    }

    showMockTimeline() {
        const mockData = [
            {
                date: '2024-07-10',
                title: 'Consultation with Dr. Smith',
                description: 'Regular check-up and medication review'
            },
            {
                date: '2024-06-15',
                title: 'Blood Test Results',
                description: 'All parameters within normal range'
            },
            {
                date: '2024-05-20',
                title: 'MRI Scan',
                description: 'Brain scan for migraine investigation'
            }
        ];
        
        this.displayTimeline(mockData);
    }

    displayReports(reports) {
        const reportsGrid = document.querySelector('.reports-grid');
        if (!reportsGrid) return;

        reportsGrid.innerHTML = '';
        
        reports.forEach(report => {
            const reportCard = document.createElement('div');
            reportCard.className = 'report-card';
            reportCard.innerHTML = `
                <h3>${report.title}</h3>
                <p>Latest: ${new Date(report.date).toLocaleDateString()}</p>
                <button class="btn btn-primary" onclick="window.dashboardManager.viewReport('${report.id}')">
                    View Report
                </button>
            `;
            reportsGrid.appendChild(reportCard);
        });
    }

    showMockReports() {
        const mockReports = [
            {
                id: '1',
                title: 'Blood Test Results',
                date: '2024-07-01'
            },
            {
                id: '2',
                title: 'MRI Brain Scan',
                date: '2024-06-15'
            },
            {
                id: '3',
                title: 'Cardiology Report',
                date: '2024-05-30'
            }
        ];
        
        this.displayReports(mockReports);
    }

    initializeHealthChart() {
        const canvas = document.getElementById('health-chart');
        if (!canvas) return;

        // Simple mock chart implementation
        const ctx = canvas.getContext('2d');
        canvas.width = 800;
        canvas.height = 400;

        // Draw mock health trend chart
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(50, 350);
        ctx.lineTo(150, 200);
        ctx.lineTo(250, 180);
        ctx.lineTo(350, 220);
        ctx.lineTo(450, 160);
        ctx.lineTo(550, 140);
        ctx.lineTo(650, 170);
        ctx.stroke();

        // Add labels
        ctx.fillStyle = '#333';
        ctx.font = '14px Arial';
        ctx.fillText('Health Trend Over Time', 300, 30);
    }

    handleSearch(query) {
        if (!query.trim()) return;

        // Implement search functionality
        console.log('Searching for:', query);
        
        // You could search through health data, documents, etc.
        this.performSearch(query);
    }

    async performSearch(query) {
        try {
            // Search using AI agents
            const results = await window.apiService.getAgentResponse(query, 'search');
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    displaySearchResults(results) {
        // Display search results in a modal or dedicated area
        console.log('Search results:', results);
    }

    showOrganDetails(organ) {
        // Show detailed information about the selected organ
        const details = this.getOrganDetails(organ);
        this.showModal('Organ Details', details);
    }

    getOrganDetails(organ) {
        const organData = {
            shoulder: {
                status: 'Severe Pain',
                lastCheck: '2024-07-10',
                recommendations: ['Physical therapy', 'Pain management', 'Follow-up in 2 weeks']
            },
            lungs: {
                status: 'Mild Congestion',
                lastCheck: '2024-07-08',
                recommendations: ['Monitor breathing', 'Stay hydrated', 'Avoid allergens']
            },
            liver: {
                status: 'Healthy',
                lastCheck: '2024-07-01',
                recommendations: ['Maintain current diet', 'Regular exercise', 'Annual check-up']
            },
            kidneys: {
                status: 'Under Monitoring',
                lastCheck: '2024-07-05',
                recommendations: ['Increase water intake', 'Reduce sodium', 'Monthly blood tests']
            }
        };

        return organData[organ] || {};
    }

    showModal(title, content) {
        // Create and show a modal dialog
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>Status:</strong> ${content.status || 'Unknown'}</p>
                    <p><strong>Last Check:</strong> ${content.lastCheck || 'N/A'}</p>
                    <div><strong>Recommendations:</strong></div>
                    <ul>
                        ${(content.recommendations || []).map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal events
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.classList.contains('modal-close')) {
                modal.remove();
            }
        });
    }

    selectYear(year) {
        // Update active year
        document.querySelectorAll('.year').forEach(y => y.classList.remove('active'));
        event.target.classList.add('active');

        // Load data for selected year
        this.loadDataForYear(year);
    }

    async loadDataForYear(year) {
        try {
            // Load health data for specific year
            console.log('Loading data for year:', year);
            // Implementation would filter data by year
        } catch (error) {
            console.error('Failed to load year data:', error);
        }
    }

    startVoiceRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                console.log('Voice recognition started');
                document.querySelector('.voice-btn').classList.add('listening');
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Voice input:', transcript);
                this.handleVoiceCommand(transcript);
            };

            recognition.onerror = (event) => {
                console.error('Voice recognition error:', event.error);
            };

            recognition.onend = () => {
                document.querySelector('.voice-btn').classList.remove('listening');
            };

            recognition.start();
        } else {
            alert('Voice recognition not supported in this browser');
        }
    }

    async handleVoiceCommand(command) {
        try {
            // Send voice command to AI agent
            const response = await window.apiService.chatWithAgent(command, {
                type: 'voice_command',
                current_page: this.currentPage
            });
            
            this.handleAgentResponse(response);
        } catch (error) {
            console.error('Voice command failed:', error);
        }
    }

    handleAgentResponse(response) {
        // Handle AI agent response
        console.log('Agent response:', response);
        
        // Could trigger navigation, show information, etc.
        if (response.action) {
            this.executeAgentAction(response.action);
        }
    }

    executeAgentAction(action) {
        switch (action.type) {
            case 'navigate':
                this.navigateToPage(action.page);
                break;
            case 'show_info':
                this.showModal(action.title, action.content);
                break;
            case 'search':
                this.handleSearch(action.query);
                break;
        }
    }

    async checkServiceHealth() {
        const backendHealth = await window.apiService.checkBackendHealth();
        const agentsHealth = await window.apiService.checkAgentsHealth();

        if (!backendHealth) {
            console.warn('Backend service is not available');
            this.showServiceWarning('Backend service is not available. Some features may not work.');
        }

        if (!agentsHealth) {
            console.warn('AI Agents service is not available');
            this.showServiceWarning('AI Agents service is not available. Chat and insights may not work.');
        }
    }

    showServiceWarning(message) {
        const warning = document.createElement('div');
        warning.className = 'service-warning';
        warning.textContent = message;
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff9800;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        document.body.appendChild(warning);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            warning.remove();
        }, 5000);
    }

    viewReport(reportId) {
        // View specific report
        console.log('Viewing report:', reportId);
        // Implementation would open report viewer
    }
}

// Initialize dashboard manager
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard')) {
        window.dashboardManager = new DashboardManager();
    }
});
