/**
 * Enhanced Digital Twin Health Dashboard - Main Application
 * Interactive health monitoring dashboard with Expert Opinion and Timeline features
 */

class EnhancedHealthDashboard {
  constructor(apiBaseUrl = null) {
    // Use the global API service if available, otherwise create a fallback
    this.api = window.digitalTwinAPI || {
      baseURL: apiBaseUrl || 'http://localhost:8000',
      getRegionData: this.fallbackFetch.bind(this),
      getYearData: this.fallbackFetch.bind(this),
      searchHealthData: this.fallbackSearch.bind(this),
      exportHealthData: this.fallbackExport.bind(this)
    };
    
    this.cache = new Map();
    this.timelineCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.expertMode = false;
    this.init();
  }

  // Fallback fetch method if API service is not available
  async fallbackFetch(endpoint) {
    const url = endpoint.includes('http') ? endpoint : `${this.api.baseURL}${endpoint}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  }

  async fallbackSearch(query) {
    if (!query || query.length < 2) return [];
    const response = await fetch(`${this.api.baseURL}/api/health/search?q=${encodeURIComponent(query)}`);
    return response.ok ? response.json() : [];
  }

  async fallbackExport() {
    const response = await fetch(`${this.api.baseURL}/api/health/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: 'pdf' })
    });
    return response.blob();
  }

  init() {
    this.setupEventListeners();
    this.setupAnimations();
    this.initializeMockData();
    console.log('Enhanced Digital Twin Health Dashboard initialized');
  }

  setupEventListeners() {
    // Body region markers
    const regionMarkers = document.querySelectorAll('[data-region]');
    regionMarkers.forEach(marker => {
      marker.addEventListener('click', (e) => {
        const region = e.currentTarget.getAttribute('data-region');
        this.loadTimeline(region);
        this.highlightActiveRegion(e.currentTarget);
      });
    });

    // Timeline year items
    const yearItems = document.querySelectorAll('[data-year]');
    yearItems.forEach(item => {
      item.addEventListener('click', (e) => {
        const year = e.currentTarget.getAttribute('data-year');
        this.fetchYearData(year);
        this.highlightActiveYear(e.currentTarget);
      });
    });

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.handleSearch(e.target.value);
      });
    }

    // Export button
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        this.exportHealthData();
      });
    }

    // Chat functionality
    this.setupChatEventListeners();
  }

  setupChatEventListeners() {
    // Open chat panel
    const openChatBtn = document.getElementById('openChatBtn');
    if (openChatBtn) {
      openChatBtn.addEventListener('click', () => {
        this.openExpertChat();
      });
    }

    // Close chat panel
    const closeChatBtn = document.getElementById('closeChatBtn');
    if (closeChatBtn) {
      closeChatBtn.addEventListener('click', () => {
        this.closeExpertChat();
      });
    }

    // Expert mode toggle
    const expertToggle = document.getElementById('expertModeToggle');
    if (expertToggle) {
      expertToggle.addEventListener('change', (event) => {
        this.expertMode = event.target.checked;
        console.log("Expert mode is now", this.expertMode ? "ON" : "OFF");
        this.updateChatPlaceholder();
      });
    }

    // Send chat message
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatInput = document.getElementById('chatInput');
    
    if (sendChatBtn) {
      sendChatBtn.addEventListener('click', () => {
        this.sendChatMessage();
      });
    }

    if (chatInput) {
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          this.sendChatMessage();
        }
      });
    }

    // Close sources panel
    const closeSourcesBtn = document.getElementById('closeSourcesBtn');
    if (closeSourcesBtn) {
      closeSourcesBtn.addEventListener('click', () => {
        this.closeSourcesPanel();
      });
    }
  }

  setupAnimations() {
    // Add CSS for pulse animation if not already present
    if (!document.querySelector('#dashboard-animations')) {
      const style = document.createElement('style');
      style.id = 'dashboard-animations';
      style.textContent = `
        .pulse-animation {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: .7; transform: scale(1.1); }
        }
        .year-header {
          user-select: none;
        }
        .year-header:hover {
          background-color: rgba(59, 130, 246, 0.1);
        }
        .cite {
          cursor: pointer;
          text-decoration: underline;
        }
        .cite:hover {
          background-color: rgba(59, 130, 246, 0.2);
        }
      `;
      document.head.appendChild(style);
    }
  }

  // Timeline functionality
  async loadTimeline(region) {
    const timelinePanel = document.getElementById('timelinePanel');
    const timelineTitle = document.getElementById('timelineTitle');

    // Update the title to show selected region
    timelineTitle.textContent = `Timeline – ${region.charAt(0).toUpperCase() + region.slice(1)}`;

    // Show loading state
    timelinePanel.innerHTML = "<p class='text-gray-400'>Loading events...</p>";

    // If caching is desired and data is fresh, use cache
    if (this.timelineCache.has(region)) {
      this.renderTimeline(this.timelineCache.get(region));
      return;
    }

    try {
      // Try to fetch from API, fallback to mock data
      let events;
      try {
        const response = await fetch(`${this.api.baseURL}/api/health/timeline?region=${region}`);
        const data = await response.json();
        events = data.events || [];
      } catch (error) {
        // Use mock data if API fails
        events = this.getMockTimelineData(region);
      }

      // Cache the data
      this.timelineCache.set(region, events);
      
      // Render timeline
      this.renderTimeline(events);
    } catch (err) {
      console.error("Timeline fetch error:", err);
      timelinePanel.innerHTML = "<p class='text-red-500'>Failed to load timeline data.</p>";
    }
  }

  renderTimeline(events) {
    const timelinePanel = document.getElementById('timelinePanel');
    timelinePanel.innerHTML = "";

    if (!events.length) {
      timelinePanel.innerHTML = "<p class='text-gray-400'>No records available for this region.</p>";
      return;
    }

    // Group events by year and month
    const eventsByYear = {};
    for (let evt of events) {
      const date = new Date(evt.date);
      if (isNaN(date)) continue;
      const year = date.getFullYear();
      const month = date.toLocaleString('default', { month: 'long' });
      eventsByYear[year] = eventsByYear[year] || {};
      eventsByYear[year][month] = eventsByYear[year][month] || [];
      eventsByYear[year][month].push({ date: date, summary: evt.summary, severity: evt.severity || 'normal' });
    }

    // Sort years chronologically
    const years = Object.keys(eventsByYear).map(y => parseInt(y)).sort((a,b) => a - b);

    years.forEach(year => {
      // Year header
      const yearHeader = document.createElement('h4');
      yearHeader.textContent = year;
      yearHeader.className = "year-header text-lg font-bold mt-4 cursor-pointer flex items-center p-2 rounded-lg transition-colors duration-200";
      yearHeader.innerHTML = `▶ ${year}`;
      timelinePanel.appendChild(yearHeader);

      // Months container (initially hidden)
      const monthsContainer = document.createElement('div');
      monthsContainer.className = "ml-4 months-container hidden";
      
      // For each month in the year, sort and list events
      const months = Object.keys(eventsByYear[year]);
      const monthOrder = ["January","February","March","April","May","June","July","August","September","October","November","December"];
      months.sort((a, b) => monthOrder.indexOf(a) - monthOrder.indexOf(b));
      
      months.forEach(month => {
        const monthEvents = eventsByYear[year][month];
        // Month header
        const monthHeader = document.createElement('h5');
        monthHeader.textContent = month;
        monthHeader.className = "text-md font-semibold mt-2 text-primary-400";
        monthsContainer.appendChild(monthHeader);

        // Events under the month
        monthEvents.sort((a,b) => a.date - b.date);
        monthEvents.forEach(evt => {
          const evtItem = document.createElement('div');
          evtItem.className = "ml-6 text-sm text-gray-300 p-2 rounded border-l-2 border-gray-600 mb-2";
          
          // Color code by severity
          const severityColors = {
            'severe': 'border-red-500 bg-red-900 bg-opacity-20',
            'moderate': 'border-yellow-500 bg-yellow-900 bg-opacity-20',
            'mild': 'border-green-500 bg-green-900 bg-opacity-20',
            'normal': 'border-blue-500 bg-blue-900 bg-opacity-20'
          };
          
          evtItem.className += ` ${severityColors[evt.severity] || severityColors.normal}`;
          
          const day = evt.date.getDate();
          const mon = evt.date.toLocaleString('default', { month: 'short' });
          evtItem.innerHTML = `<strong>${mon} ${day}:</strong> ${evt.summary}`;
          monthsContainer.appendChild(evtItem);
        });
      });

      timelinePanel.appendChild(monthsContainer);

      // Toggle month visibility on year click
      yearHeader.addEventListener('click', () => {
        const isHidden = monthsContainer.classList.contains('hidden');
        monthsContainer.classList.toggle('hidden');
        yearHeader.innerHTML = (isHidden ? "▼ " : "▶ ") + year;
      });
    });
  }

  // Chat functionality
  openExpertChat() {
    const chatPanel = document.getElementById('expertChatPanel');
    chatPanel.classList.remove('hidden');
  }

  closeExpertChat() {
    const chatPanel = document.getElementById('expertChatPanel');
    chatPanel.classList.add('hidden');
    this.closeSourcesPanel();
  }

  closeSourcesPanel() {
    const sourcesPanel = document.getElementById('expertSourcesPanel');
    sourcesPanel.classList.add('hidden');
  }

  updateChatPlaceholder() {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.placeholder = this.expertMode 
        ? "Ask for a deep research analysis..."
        : "Ask about your health...";
    }
  }

  async sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;

    // Clear input
    chatInput.value = '';

    // Add user message to chat
    this.addChatMessage(message, 'user');

    // Determine endpoint based on expert mode
    const endpoint = this.expertMode 
      ? '/api/health/expert_opinion'
      : '/api/health/chat';

    try {
      // Show typing indicator
      this.showTypingIndicator();

      let response;
      try {
        // Try real API first
        const apiResponse = await fetch(`${this.api.baseURL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: message })
        });
        response = await apiResponse.json();
      } catch (error) {
        // Fallback to mock response
        response = this.getMockChatResponse(message, this.expertMode);
      }

      this.hideTypingIndicator();

      if (this.expertMode) {
        this.displayExpertResponse(response);
      } else {
        this.displayChatResponse(response);
      }
    } catch (err) {
      console.error("Error sending message:", err);
      this.hideTypingIndicator();
      this.addChatMessage("Sorry, I'm having trouble processing your request right now.", 'assistant');
    }
  }

  addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
      sender === 'user' 
        ? 'bg-primary-600 text-white' 
        : 'bg-gray-700 text-gray-100'
    }`;
    bubbleDiv.textContent = message;

    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  showTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'flex justify-start';
    typingDiv.innerHTML = `
      <div class="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg">
        <div class="flex space-x-1">
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
          <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
        </div>
      </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  displayChatResponse(response) {
    const answer = response.answer || response.message || "I'm sorry, I couldn't process that request.";
    this.addChatMessage(answer, 'assistant');
  }

  displayExpertResponse(response) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Create expert response bubble
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-start';

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'max-w-xs lg:max-w-md px-4 py-2 rounded-lg bg-gray-700 text-gray-100';
    
    // Process answer with citations
    let answerHTML = response.answer || "I couldn't generate an expert analysis.";
    answerHTML = answerHTML.replace(/\[(\d+)\]/g, '<sup class="text-primary-300 cursor-pointer cite" data-cite="$1">[$1]</sup>');
    
    bubbleDiv.innerHTML = answerHTML;
    messageDiv.appendChild(bubbleDiv);
    chatMessages.appendChild(messageDiv);

    // Handle citation clicks
    bubbleDiv.querySelectorAll('.cite').forEach(citeEl => {
      citeEl.addEventListener('click', () => {
        this.showSourcesPanel(response);
        const srcIndex = citeEl.getAttribute('data-cite');
        this.highlightSource(srcIndex);
      });
    });

    // Show sources panel if we have sources
    if (response.sources && response.sources.length > 0) {
      this.showSourcesPanel(response);
    }

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  showSourcesPanel(response) {
    const sourcesPanel = document.getElementById('expertSourcesPanel');
    const sourcesList = document.getElementById('sourcesList');
    const researchSteps = document.getElementById('researchSteps');

    // Clear previous content
    sourcesList.innerHTML = "";
    researchSteps.innerHTML = "";

    // Add research steps if available
    if (response.steps) {
      researchSteps.innerHTML = `<p><strong>Research Process:</strong> ${response.steps}</p>`;
    }

    // Populate sources
    if (response.sources) {
      response.sources.forEach((src, index) => {
        const li = document.createElement('li');
        li.className = "text-sm p-2 rounded hover:bg-gray-800 transition-colors";
        li.innerHTML = `<a href="${src.url}" target="_blank" class="underline text-primary-400 hover:text-primary-300">${src.title}</a>`;
        sourcesList.appendChild(li);
      });
    }

    // Show the panel
    sourcesPanel.classList.remove('hidden');
  }

  highlightSource(srcIndex) {
    const sourceItems = document.querySelectorAll('#sourcesList li');
    if (sourceItems[srcIndex - 1]) {
      sourceItems[srcIndex - 1].classList.add('bg-gray-800');
      setTimeout(() => sourceItems[srcIndex - 1].classList.remove('bg-gray-800'), 2000);
    }
  }

  // Existing methods (updated for new structure)
  async fetchRegionData(region) {
    this.showLoadingState();
    try {
      let data;
      try {
        data = await this.api.getRegionData(`/api/health/region/${region}`);
      } catch (error) {
        data = this.getMockRegionData(region);
      }
      this.displayRegionData(data, region);
    } catch (error) {
      this.showError('Failed to load region data');
    }
    this.hideLoadingState();
  }

  async fetchYearData(year) {
    this.showLoadingState();
    try {
      let data;
      try {
        data = await this.api.getYearData(`/api/health/history/${year}`);
      } catch (error) {
        data = this.getMockYearData(year);
      }
      this.displayYearData(data, year);
    } catch (error) {
      this.showError('Failed to load year data');
    }
    this.hideLoadingState();
  }

  displayRegionData(data, region) {
    const panel = document.getElementById('timelinePanel');
    if (!panel) return;

    panel.innerHTML = `
      <div class="space-y-4">
        <h3 class="text-lg font-semibold text-white capitalize">${region} Health Data</h3>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-gray-600 p-3 rounded-lg">
            <p class="text-xs text-gray-400">Status</p>
            <p class="text-sm font-medium text-white">${data.status || 'Normal'}</p>
          </div>
          <div class="bg-gray-600 p-3 rounded-lg">
            <p class="text-xs text-gray-400">Last Check</p>
            <p class="text-sm font-medium text-white">${data.lastCheck || '2024-07-15'}</p>
          </div>
        </div>
        <div class="space-y-2">
          <h4 class="text-sm font-medium text-gray-300">Recent Activity</h4>
          ${(data.activities || []).map(activity => 
            `<div class="bg-gray-600 p-2 rounded text-xs">
              <span class="text-gray-400">${activity.date}</span> - ${activity.description}
            </div>`
          ).join('')}
        </div>
      </div>
    `;
  }

  displayYearData(data, year) {
    const panel = document.getElementById('timelinePanel');
    if (!panel) return;

    panel.innerHTML = `
      <div class="space-y-4">
        <h3 class="text-lg font-semibold text-white">${year} Health Summary</h3>
        <div class="grid grid-cols-1 gap-3">
          ${(data.summary || []).map(item => 
            `<div class="bg-gray-600 p-3 rounded-lg">
              <h4 class="text-sm font-medium text-white">${item.title}</h4>
              <p class="text-xs text-gray-300">${item.description}</p>
            </div>`
          ).join('')}
        </div>
      </div>
    `;
  }

  async handleSearch(query) {
    const resultsContainer = document.getElementById('search-results');
    
    if (!query || query.length < 2) {
      resultsContainer.classList.add('hidden');
      return;
    }

    try {
      let results;
      try {
        results = await this.api.searchHealthData(query);
      } catch (error) {
        results = this.getMockSearchResults(query);
      }
      
      this.displaySearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    }
  }

  displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!results || results.length === 0) {
      container.classList.add('hidden');
      return;
    }

    container.innerHTML = results.map(result => `
      <div class="p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors duration-200">
        <h4 class="text-sm font-medium text-white">${result.title}</h4>
        <p class="text-xs text-gray-400">${result.description}</p>
        <span class="text-xs text-primary-400">${result.date}</span>
      </div>
    `).join('');
    
    container.classList.remove('hidden');
  }

  async exportHealthData() {
    try {
      const blob = await this.api.exportHealthData();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'health-data-export.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      alert('Export functionality will be available when connected to the backend.');
    }
  }

  highlightActiveRegion(marker) {
    // Remove active class from all markers
    document.querySelectorAll('.health-marker').forEach(m => 
      m.classList.remove('ring-2', 'ring-primary-500'));
    
    // Add active class to clicked marker
    marker.classList.add('ring-2', 'ring-primary-500');
  }

  highlightActiveYear(yearItem) {
    // Remove active class from all year items
    document.querySelectorAll('.year-item').forEach(item => {
      item.classList.remove('bg-primary-600', 'text-white');
      item.classList.add('bg-gray-700', 'text-gray-300');
    });
    
    // Add active class to clicked year
    yearItem.classList.remove('bg-gray-700', 'text-gray-300');
    yearItem.classList.add('bg-primary-600', 'text-white');
  }

  showLoadingState() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) indicator.classList.remove('hidden');
  }

  hideLoadingState() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) indicator.classList.add('hidden');
  }

  showError(message) {
    console.error(message);
    // Could add toast notification here
  }

  // Mock data methods
  initializeMockData() {
    // Initialize any mock data needed for offline functionality
    console.log('Mock data initialized for offline testing');
  }

  getMockTimelineData(region) {
    const mockData = {
      head: [
        { date: '2024-06-15', summary: 'Routine neurological checkup - all normal', severity: 'normal' },
        { date: '2024-03-10', summary: 'Mild headache reported, stress-related', severity: 'mild' },
        { date: '2023-11-20', summary: 'Annual brain MRI scan - no abnormalities', severity: 'normal' },
        { date: '2023-08-05', summary: 'Consultation for sleep disorders', severity: 'moderate' }
      ],
      heart: [
        { date: '2024-07-01', summary: 'Cardiovascular health assessment - excellent', severity: 'normal' },
        { date: '2024-04-15', summary: 'Blood pressure monitoring - slightly elevated', severity: 'mild' },
        { date: '2024-01-30', summary: 'Cholesterol levels check - within normal range', severity: 'normal' },
        { date: '2023-10-12', summary: 'ECG performed - normal sinus rhythm', severity: 'normal' }
      ],
      lungs: [
        { date: '2024-06-20', summary: 'Respiratory function test - normal capacity', severity: 'normal' },
        { date: '2024-02-28', summary: 'Chest X-ray for persistent cough', severity: 'mild' },
        { date: '2023-12-15', summary: 'Annual lung function assessment', severity: 'normal' },
        { date: '2023-09-08', summary: 'Bronchitis treatment completed successfully', severity: 'moderate' }
      ],
      liver: [
        { date: '2024-05-25', summary: 'Liver enzyme levels - all within normal range', severity: 'normal' },
        { date: '2024-02-14', summary: 'Hepatitis B vaccination booster', severity: 'normal' },
        { date: '2023-11-30', summary: 'Alcohol consumption counseling session', severity: 'mild' },
        { date: '2023-08-18', summary: 'Liver ultrasound - no abnormalities detected', severity: 'normal' }
      ],
      kidneys: [
        { date: '2024-06-10', summary: 'Kidney function test - excellent results', severity: 'normal' },
        { date: '2024-03-25', summary: 'Urinalysis completed - no issues found', severity: 'normal' },
        { date: '2024-01-12', summary: 'Hydration counseling and lifestyle advice', severity: 'normal' },
        { date: '2023-10-05', summary: 'Kidney stone prevention consultation', severity: 'mild' }
      ],
      stomach: [
        { date: '2024-06-30', summary: 'Digestive health checkup - all systems normal', severity: 'normal' },
        { date: '2024-04-08', summary: 'Treatment for acid reflux - symptoms resolved', severity: 'mild' },
        { date: '2024-01-22', summary: 'Dietary consultation for IBS management', severity: 'moderate' },
        { date: '2023-11-14', summary: 'Colonoscopy screening - no abnormalities', severity: 'normal' }
      ],
      shoulder: [
        { date: '2024-07-05', summary: 'Physical therapy session - improved mobility', severity: 'normal' },
        { date: '2024-04-20', summary: 'Shoulder pain management - cortisone injection', severity: 'moderate' },
        { date: '2024-02-10', summary: 'Rotator cuff assessment - minor strain detected', severity: 'mild' },
        { date: '2023-12-01', summary: 'Shoulder X-ray - no structural damage', severity: 'normal' }
      ]
    };

    return mockData[region] || [];
  }

  getMockChatResponse(message, isExpertMode) {
    if (isExpertMode) {
      return {
        answer: `Based on comprehensive analysis of your health data and current medical literature, here are the key insights regarding "${message}": This represents a thorough research-backed response [1][2]. Multiple data sources have been consulted to provide you with the most accurate information [3].`,
        sources: [
          { id: 1, title: "Clinical Guidelines for Patient Care 2024", url: "https://example.com/guidelines" },
          { id: 2, title: "Recent Medical Research on Related Conditions", url: "https://example.com/research" },
          { id: 3, title: "Patient Health Data Analysis Report", url: "https://example.com/analysis" }
        ],
        steps: "Analyzed patient history, consulted medical databases, reviewed recent studies, cross-referenced with clinical guidelines."
      };
    } else {
      return {
        answer: `Thank you for your question about "${message}". Based on your health profile, I can provide some general guidance. For specific medical advice, please consult with Dr. Ericsson.`
      };
    }
  }

  getMockRegionData(region) {
    return {
      status: 'Normal',
      lastCheck: '2024-07-15',
      activities: [
        { date: '2024-07-10', description: 'Routine checkup completed' },
        { date: '2024-06-25', description: 'Lab results reviewed' }
      ]
    };
  }

  getMockYearData(year) {
    return {
      summary: [
        { title: 'Health Assessments', description: `${year} saw regular health monitoring with positive outcomes` },
        { title: 'Preventive Care', description: 'All scheduled preventive care completed successfully' },
        { title: 'Treatment Plans', description: 'Ongoing treatment plans showing good progress' }
      ]
    };
  }

  getMockSearchResults(query) {
    return [
      {
        title: `Health record: ${query}`,
        description: 'Relevant health information found in your medical history',
        date: '2024-07-10'
      },
      {
        title: `Lab result: ${query}`,
        description: 'Laboratory test results matching your search',
        date: '2024-06-15'
      }
    ];
  }
}

// Initialize the enhanced dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.enhancedDashboard = new EnhancedHealthDashboard();
});
