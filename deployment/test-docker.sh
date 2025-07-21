#!/bin/bash
# Quick Docker Compose V2 verification script
set -e

echo "🐳 Testing Docker Compose V2 Setup..."
echo "======================================"

# Check Docker and Docker Compose versions
echo "📋 Checking versions:"
docker --version
docker compose version

echo ""
echo "🔍 Validating Docker Compose files:"

# Validate main compose file
if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml - Valid"
else
    echo "❌ docker-compose.yml - Invalid"
    exit 1
fi

# Validate UV override file
if docker compose -f docker-compose.yml -f docker-compose.uv.yml config > /dev/null 2>&1; then
    echo "✅ docker-compose.uv.yml override - Valid"
else
    echo "❌ docker-compose.uv.yml override - Invalid"
    exit 1
fi

echo ""
echo "🚀 Docker Compose configuration is valid!"
echo "Ready to deploy with: ./deploy-uv.sh up"
