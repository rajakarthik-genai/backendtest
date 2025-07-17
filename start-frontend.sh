#!/bin/bash

# Digital Twin Health Dashboard Startup Script
echo "🏥 Starting Digital Twin Health Dashboard..."
echo "================================================"

# Check if port 3000 is available
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use"
    echo "🔍 Finding available port..."
    PORT=3001
    while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
        ((PORT++))
    done
else
    PORT=3000
fi

echo "🌐 Starting server on port $PORT..."
echo "📱 Dashboard will be available at: http://localhost:$PORT"
echo ""
echo "🧪 Mock API is enabled - no backend required for testing"
echo "📊 Click on body regions or timeline years to see health data"
echo "💡 Press Ctrl+C to stop the server"
echo ""

# Check if Python is available and start server
if command -v python3 &> /dev/null; then
    echo "✅ Using Python 3..."
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    echo "✅ Using Python..."
    python -m http.server $PORT
else
    echo "❌ Python not found. Please install Python or use another web server."
    echo ""
    echo "Alternative methods:"
    echo "1. Install Python: https://python.org/downloads"
    echo "2. Use Node.js: npx serve . -p $PORT"
    echo "3. Use PHP: php -S localhost:$PORT"
    echo "4. Use any other web server to serve static files"
    exit 1
fi
