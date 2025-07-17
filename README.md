# MediTwin Digital Health Dashboard

A modern, responsive digital twin health dashboard with AI-powered medical insights and comprehensive user authentication.

## Features

- **Authentication System**: Complete login/signup with JWT token management
- **Interactive Body Map**: 7 health regions with clickable markers and tooltips
- **Timeline Interface**: Year/month drill-down navigation with health data
- **Expert Opinion Chat**: AI-powered medical chat with citation panel
- **Agent Service Integration**: Comprehensive medical analysis and knowledge base
- **Modern UI**: Tailwind CSS with dark theme and mobile responsiveness
- **Export Functions**: PDF export and data visualization
- **Real-time Testing**: Built-in agent service testing panel

## Quick Start

1. **Start the frontend**:
   ```bash
   ./start-frontend.sh
   ```

2. **Access the application**:
   - Authentication: `http://localhost:3000/auth.html`
   - Dashboard: `http://localhost:3000/index.html`

## Backend Integration

- **Login Service**: `https://lenient-sunny-grouse.ngrok-free.app`
- **Agent Service**: `https://mackerel-liberal-loosely.ngrok-free.app`

## File Structure

```
├── auth.html              # Authentication page (login/signup)
├── index.html             # Main dashboard
├── app.js                 # Dashboard application logic
├── mock-api.js            # Mock API for offline testing
├── start-frontend.sh      # Server startup script
├── js/
│   ├── api.js             # Main API service
│   ├── auth.js            # Authentication manager
│   ├── chat.js            # Chat manager
│   ├── config.js          # Base configuration
│   ├── digital-twin-api.js    # Digital twin API
│   ├── digital-twin-config.js # Dashboard configuration
│   └── agent-tester.js    # Agent service testing panel
└── styles/
    ├── auth.css           # Authentication styles
    └── dashboard.css      # Dashboard styles
```

## Usage

1. **Authentication**: Sign up or login at `/auth.html`
2. **Dashboard**: Explore health regions, timeline, and chat features
3. **Agent Testing**: Click "Test Agents" in sidebar to test all endpoints
4. **Export Data**: Use export button for PDF reports

## Technology Stack

- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Authentication**: JWT tokens with secure storage
- **API Integration**: RESTful APIs with error handling
- **Responsive Design**: Mobile-first approach
- **Development**: Python HTTP server for local testing
