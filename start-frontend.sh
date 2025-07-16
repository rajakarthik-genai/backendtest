#!/bin/bash

echo "🚀 Starting MediTwin Frontend..."

# Check if port 3000 is available
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 3000 is already in use"
    echo "🔍 Finding available port..."
    PORT=3001
    while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; do
        ((PORT++))
    done
else
    PORT=3000
fi

echo "🌐 Starting server on port $PORT..."

if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m http.server $PORT
else
    echo "❌ Python not found. Please install Python to run the frontend."
    exit 1
fi
