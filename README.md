# MediTwin Frontend

A comprehensive web-based frontend for the MediTwin Digital Twin Healthcare Platform. This application provides an intuitive interface for medical professionals and patients to interact with AI-powered healthcare services.

## 🧪 Testing

### Complete User Journey Test
The project includes a single comprehensive test file that validates the entire user journey:

**File:** `complete_user_journey_test.py`

**Features Tested:**
- ✅ User Registration (Signup)
- ✅ User Authentication (Login)
- ✅ User Profile Access
- ✅ All AI Agents Service Endpoints
- ✅ Medical Analysis & Recommendations
- ✅ Knowledge Base & Drug Interactions
- ✅ Analytics & Health Scoring
- ✅ Chat & Messaging Services

**Usage:**
```bash
# Run the complete test suite
python3 complete_user_journey_test.py
```

**Requirements:**
- Backend Auth Service running on `localhost:8081`
- Agents Service running on `localhost:8000`
- Python packages: `requests`

## 🏥 Features

### Authentication
- **Secure Login/Signup**: User authentication with JWT tokens
- **Password Validation**: Client-side validation for strong passwords
- **Remember Me**: Persistent login sessions
- **Auto-logout**: Session timeout handling

### Dashboard
- **Human Body Model**: Interactive 3D-like body visualization with health indicators
- **Health Summary**: Real-time health data overview
- **Medical Timeline**: Chronological view of medical events
- **Data Visualization**: Charts and graphs for health trends
- **Search Functionality**: Global search across medical data

### AI Chat Assistant
- **Natural Language Processing**: Chat with AI medical assistant
- **Medical Insights**: AI-powered health analysis and recommendations
- **Voice Recognition**: Voice-to-text input support
- **Chat History**: Persistent conversation history
- **Smart Suggestions**: Context-aware response suggestions

### Document Management
- **File Upload**: Drag-and-drop document upload
- **Format Support**: PDF, DOC, DOCX, images (JPG, PNG, GIF)
- **AI Analysis**: Automatic document analysis with medical entity extraction
- **Document Viewer**: In-browser document viewing
- **Secure Storage**: Encrypted document storage

### Health Analysis
- **Symptom Tracking**: Track and analyze symptoms over time
- **Medication Management**: Track medications and interactions
- **Report Generation**: Generate comprehensive health reports
- **Trend Analysis**: Identify patterns in health data

## 🛠 Technology Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Modern CSS with Flexbox/Grid, Font Awesome icons
- **API Integration**: RESTful APIs with fetch()
- **State Management**: Local storage for session management
- **Responsive Design**: Mobile-first responsive layout

## 📁 Project Structure

```
meditwin-frontend/
├── index.html              # Main HTML file with all pages
├── styles/
│   ├── main.css            # Main stylesheet with dashboard styles
│   └── auth.css            # Authentication page styles
├── js/
│   ├── api.js              # API service layer and configuration
│   ├── auth.js             # Authentication management
│   ├── dashboard.js        # Dashboard functionality
│   ├── chat.js             # AI chat features
│   ├── documents.js        # Document upload and management
│   └── main.js             # Application controller and utilities
├── test-frontend.sh        # Comprehensive testing script
├── start-frontend.sh       # Frontend startup script (auto-generated)
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.x (for local development server)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Backend services running:
  - `~/backend/meditwin-backend` (Authentication & Medical Data API)
  - `~/agents/meditwin-agents` (AI Agents Service)

### Installation & Setup

1. **Clone or navigate to the frontend directory**:
   ```bash
   cd /home/user/frontend/meditwin-frontend
   ```

2. **Test the frontend**:
   ```bash
   chmod +x test-frontend.sh
   ./test-frontend.sh
   ```

3. **Start the development server**:
   ```bash
   # Option 1: Use the generated startup script
   ./start-frontend.sh
   
   # Option 2: Manual start
   python3 -m http.server 8080
   ```

4. **Open in browser**:
   ```
   http://localhost:8080
   ```

## 🔧 Configuration

### Backend Services Configuration

The frontend is configured to connect to your backend services at:

- **Authentication Service**: `http://localhost:8000` (meditwin-backend)
- **AI Agents Service**: `http://localhost:8001` (meditwin-agents)

To modify these URLs, edit `js/api.js`:

```javascript
constructor() {
    this.backendBaseURL = 'http://localhost:8000';  // Your backend URL
    this.agentsBaseURL = 'http://localhost:8001';   // Your agents URL
}
```

### API Endpoints

The frontend integrates with the following API endpoints:

#### Authentication (meditwin-backend)
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user profile
- `PUT /auth/profile` - Update user profile

#### Medical Data (meditwin-backend)
- `GET /api/health/data` - Get health data
- `GET /api/medical/history` - Get medical history
- `GET /api/reports` - Get medical reports
- `POST /api/documents/upload` - Upload medical documents
- `GET /api/documents` - List documents
- `DELETE /api/documents/:id` - Delete document

#### AI Agents (meditwin-agents)
- `POST /api/chat` - Chat with AI assistant
- `POST /api/agents/query` - General AI queries
- `POST /api/agents/analyze-document` - Document analysis
- `POST /api/agents/health-insights` - Health insights
- `POST /api/agents/diagnostic-suggestions` - Diagnostic suggestions
- `POST /api/agents/treatment-recommendations` - Treatment recommendations

## 🎯 Usage Guide

### 1. Authentication

**Login**:
- Navigate to the login page (default view)
- Enter email and password
- Click "Login" to authenticate

**Signup**:
- Click "Sign up" link on login page
- Fill in required information
- Create account and return to login

### 2. Dashboard Navigation

**Sidebar Menu**:
- **Dashboard**: Main health overview
- **Timeline**: Medical history timeline
- **Reports**: Medical reports and test results
- **Analysis**: Health trend analysis
- **AI Chat**: Chat with medical AI assistant
- **Documents**: Upload and manage medical documents
- **Settings**: User profile and preferences

### 3. AI Chat Assistant

**Starting a Chat**:
- Navigate to "AI Chat" in sidebar
- Type your medical question
- Press Enter or click send button
- Receive AI-powered responses with medical insights

**Voice Input**:
- Click microphone button to use voice input
- Speak your question clearly
- AI will process and respond

### 4. Document Upload

**Upload Process**:
- Navigate to "Documents" section
- Drag and drop files or click "Upload Document"
- Supported formats: PDF, DOC, DOCX, JPG, PNG, GIF
- Maximum file size: 10MB per file

**AI Analysis**:
- Click "Analyze" button on uploaded documents
- AI will extract medical entities and insights
- View analysis results in modal dialog

### 5. Health Data Visualization

**Interactive Body Model**:
- Click on colored indicators on the body model
- View detailed organ-specific information
- See health status and recommendations

**Health Timeline**:
- View chronological medical events
- Filter by date ranges
- Export timeline data

## 🔧 Development

### Running Tests

```bash
# Run comprehensive frontend tests
./test-frontend.sh
```

The test script checks:
- File structure integrity
- HTML validation
- JavaScript syntax
- CSS syntax
- Local server functionality
- API configuration
- Responsive design
- Accessibility features

### Adding New Features

1. **Create new JavaScript module** in `js/` directory
2. **Add styles** in appropriate CSS file
3. **Update HTML** structure if needed
4. **Register module** in `main.js`
5. **Test functionality** with test script

### Debugging

**Browser Developer Tools**:
- Open browser DevTools (F12)
- Check Console for JavaScript errors
- Monitor Network tab for API calls
- Use Elements tab for styling issues

**Common Issues**:
- **CORS Errors**: Ensure backend services have CORS enabled
- **API Connection**: Verify backend services are running
- **File Upload**: Check file size and format restrictions

## 🔐 Security Features

- **JWT Token Management**: Secure token storage and refresh
- **Input Validation**: Client-side form validation
- **XSS Protection**: Sanitized user inputs
- **HTTPS Ready**: Designed for HTTPS deployment
- **Session Management**: Automatic logout on inactivity

## 📱 Responsive Design

The frontend is fully responsive and works on:
- **Desktop**: Full-featured dashboard experience
- **Tablet**: Optimized layout for touch interface
- **Mobile**: Condensed navigation with essential features

Breakpoints:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## 🚀 Deployment

### Production Deployment

1. **Build optimization** (if using build tools):
   ```bash
   # Minify CSS and JavaScript
   # Optimize images
   # Generate production config
   ```

2. **Server configuration**:
   ```nginx
   # Nginx configuration example
   server {
       listen 80;
       server_name your-domain.com;
       root /path/to/meditwin-frontend;
       index index.html;
       
       location / {
           try_files $uri $uri/ /index.html;
       }
       
       location /api/ {
           proxy_pass http://backend-server:8000;
       }
   }
   ```

3. **Environment variables**:
   ```javascript
   // Update API URLs for production
   const config = {
       backendURL: process.env.BACKEND_URL || 'https://api.meditwin.com',
       agentsURL: process.env.AGENTS_URL || 'https://agents.meditwin.com'
   };
   ```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section below
- Review browser console for errors
- Verify backend services are running
- Contact development team

## 🔧 Troubleshooting

### Common Issues

**"Failed to load resource" errors**:
- Verify backend services are running
- Check API URLs in `js/api.js`
- Ensure CORS is configured on backend

**Login not working**:
- Check browser developer tools for errors
- Verify credentials
- Ensure backend authentication service is running

**File upload fails**:
- Check file size (max 10MB)
- Verify file format is supported
- Check browser console for errors

**Chat not responding**:
- Verify AI agents service is running
- Check network connectivity
- Review browser console for API errors

**Styling issues**:
- Clear browser cache
- Check if CSS files are loading
- Verify no conflicting styles

### Browser Compatibility

**Minimum Requirements**:
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

**Features requiring modern browsers**:
- Speech Recognition (Chrome/Edge)
- File API for drag-and-drop
- Fetch API for network requests

---

🏥 **MediTwin Frontend** - Empowering Digital Twin Healthcare Technology
