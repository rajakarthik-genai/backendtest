# Enhanced Digital Twin Health Dashboard

A comprehensive, interactive health monitoring dashboard with Expert Opinion AI assistance and advanced timeline features.

## 🌟 New Features

### 1. Expert Opinion Mode
- **Deep Research Toggle**: Switch between normal chat and expert research mode
- **Multi-Agent AI**: Powered by CrewAI agents using Neo4j, Milvus, and web sources
- **Citation Support**: All expert answers include numbered citations [1][2][3]
- **Sources Panel**: ChatGPT-style sidebar showing research sources and process
- **Research Transparency**: View the steps taken to generate each expert response

### 2. Interactive Timeline
- **Body Region Filtering**: Click any body part to see its specific medical timeline
- **Year/Month Drill-down**: Expandable timeline organized by year and month
- **Severity Color Coding**: Visual indicators for normal, mild, moderate, and severe events
- **Event Categorization**: Organized by date with detailed summaries

### 3. Enhanced UI/UX
- **Dr. Ericsson Profile**: Updated persona from "Dr. Smith" to "Dr. Ericsson"
- **Glassmorphism Effects**: Modern backdrop blur and transparency effects
- **Responsive Design**: Fully responsive across desktop, tablet, and mobile
- **Smooth Animations**: Pulse animations, hover effects, and transitions

### 4. Advanced Chat System
- **Dual Mode Operation**: Normal and Expert Opinion modes
- **Real-time Typing Indicators**: Shows when AI is processing
- **Message History**: Persistent chat history during session
- **Rich Text Support**: Supports citations, links, and formatted responses

## 🚀 Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Python 3.8+ (for backend)
- Node.js 16+ (optional, for advanced development)

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd meditwin-frontend
   chmod +x start-frontend.sh
   ```

2. **Start the Dashboard**
   ```bash
   ./start-frontend.sh
   ```

3. **Access the Dashboard**
   - Open http://localhost:3000 in your browser
   - Click on body regions to explore timeline data
   - Use the Expert Opinion chat for deep research

### With Backend Integration

1. **Start FastAPI Backend** (see BACKEND_IMPLEMENTATION_GUIDE.md)
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

2. **Update Configuration**
   - Edit `js/digital-twin-config.js`
   - Set `DEVELOPMENT_MODE: false` for production
   - Configure `API_BASE_URL` if needed

## 📊 Features Overview

### Interactive Body Map
- **7 Clickable Regions**: Head, Shoulder, Lungs, Heart, Liver, Kidneys, Stomach
- **Visual Indicators**: Pulsing markers with hover tooltips
- **Real-time Updates**: Dynamic data loading based on selection
- **Accessibility**: Keyboard navigation and screen reader support

### Timeline System
- **Regional Filtering**: Timeline specific to selected body region
- **Chronological Organization**: Events sorted by year and month
- **Event Details**: Date, summary, and severity for each medical event
- **Expandable Years**: Click year headers to expand/collapse months

### Expert Opinion Chat
- **Research Mode Toggle**: Enable deep research with citations
- **Source Attribution**: Every claim backed by numbered sources
- **Research Process**: Transparent view of analysis steps
- **Source Panel**: Clickable citations open detailed source information

### Search & Export
- **Health Data Search**: Quick search across all medical records
- **Export Functionality**: Download health data as PDF
- **Real-time Results**: Instant search with auto-complete
- **Data Filtering**: Filter by date, region, or condition type

## 🔧 Configuration

### API Endpoints
```javascript
// js/digital-twin-config.js
ENDPOINTS: {
  HEALTH: {
    TIMELINE: '/api/health/timeline',
    CHAT: '/api/health/chat',
    EXPERT_OPINION: '/api/health/expert_opinion',
    // ... other endpoints
  }
}
```

### Feature Flags
```javascript
FEATURES: {
  MOCK_API: true,           // Enable mock data for testing
  EXPERT_OPINION: true,     // Enable expert opinion mode
  TIMELINE_FILTERS: true,   // Enable timeline filtering
  EXPORT_PDF: true,         // Enable PDF export
  REAL_TIME_UPDATES: false  // Enable live data updates
}
```

### Customization
- **Colors**: Modify Tailwind config in `index.html`
- **Regions**: Add/remove body regions in config and HTML
- **Timeline**: Customize years and event types
- **Chat Responses**: Update mock responses in `mock-api.js`

## 📱 Mobile Responsiveness

- **Adaptive Layout**: Sidebar collapses on mobile
- **Touch Interactions**: Optimized for touch devices
- **Responsive Chat**: Full-screen chat on mobile
- **Gesture Support**: Swipe to navigate panels

## 🔒 Security & Privacy

- **Data Encryption**: All API communications encrypted
- **Privacy Controls**: Patient data handling compliance
- **Access Controls**: Role-based access to features
- **Audit Logging**: Track all user interactions

## 🧪 Testing

### Manual Testing
1. **Timeline Functionality**
   - Click each body region
   - Verify timeline loads correctly
   - Test year expansion/collapse
   - Check event details display

2. **Expert Opinion**
   - Toggle expert mode on/off
   - Send test questions
   - Verify sources panel appears
   - Test citation clicking

3. **Responsive Design**
   - Test on mobile devices
   - Verify chat panel behavior
   - Check timeline scrolling

### Automated Testing
```bash
# Run automated tests (if backend available)
python complete_user_journey_test.py
```

## 📁 File Structure

```
meditwin-frontend/
├── index.html                    # Main dashboard HTML
├── app.js                       # Enhanced dashboard logic
├── mock-api.js                  # Mock data and API simulation
├── js/
│   ├── digital-twin-config.js   # Configuration and endpoints
│   └── digital-twin-api.js      # API service layer
├── styles/
│   └── dashboard.css            # Custom styles and animations
├── BACKEND_IMPLEMENTATION_GUIDE.md  # Backend setup guide
├── README-DASHBOARD.md          # This file
└── start-frontend.sh           # Quick start script
```

## 🔄 API Integration

### Timeline API
```bash
GET /api/health/timeline?region=heart
Response: {
  "region": "heart",
  "events": [...]
}
```

### Expert Opinion API
```bash
POST /api/health/expert_opinion
Body: {"message": "What are my cardiovascular risk factors?"}
Response: {
  "answer": "Based on analysis... [1][2]",
  "sources": [...],
  "steps": "Research process..."
}
```

### Chat API
```bash
POST /api/health/chat
Body: {"message": "How is my health?"}
Response: {
  "answer": "Your health indicators show..."
}
```

## 🐛 Troubleshooting

### Timeline Not Loading
- Check browser console for errors
- Verify API endpoint is accessible
- Ensure mock data is enabled for testing

### Expert Mode Not Working
- Confirm expert mode toggle is enabled
- Check network requests in developer tools
- Verify backend expert opinion endpoint

### Chat Issues
- Clear browser cache and cookies
- Check if JavaScript is enabled
- Verify WebSocket connections (if using real-time)

### Mobile Issues
- Clear mobile browser cache
- Check viewport meta tag
- Test in different mobile browsers

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📞 Support

For technical support or questions:
- Check the troubleshooting section above
- Review the backend implementation guide
- Open an issue in the repository
- Contact the development team

## 🚀 Future Enhancements

- **Voice Commands**: Voice-activated navigation
- **Real-time Monitoring**: Live health data streaming
- **AI Predictions**: Predictive health analytics
- **Wearable Integration**: Apple Health, Fitbit, etc.
- **Telemedicine**: Video consultation integration
- **Multi-language Support**: International localization

---

**Enhanced Digital Twin Health Dashboard** - Empowering patients with intelligent health insights through advanced AI and interactive visualizations.
