#!/bin/bash
# Docker deployment script using UV
set -e

cd "$(dirname "$0")"

echo "🐳 MediTwin Docker Deployment Script (with UV)"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    echo "Creating example .env file..."
    cat > .env << 'EOF'
# Database Configuration
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=your_secure_password_here
MONGODB_URI=mongodb://admin:your_secure_password_here@mongo:27017/meditwin?authSource=admin

# Neo4j Configuration  
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_secure_password_here

# Redis Configuration
REDIS_URL=redis://redis:6379

# Milvus Configuration
MILVUS_URI=http://milvus:19530

# API Keys (replace with your actual keys)
OPENAI_API_KEY=sk-your-openai-key-here
AGENTOPS_API_KEY=your-agentops-key-here

# Application Settings
ENVIRONMENT=production
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=false
LOG_LEVEL=INFO
EOF
    print_warning "Please edit .env file with your actual configuration!"
    print_warning "Especially update passwords and API keys!"
    exit 1
fi

# Parse command line arguments
COMMAND=${1:-up}

case $COMMAND in
    "up")
        print_status "Starting MediTwin services with UV..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d
        ;;
    "build")
        print_status "Building MediTwin services with UV..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml build --no-cache
        ;;
    "rebuild")
        print_status "Rebuilding and starting MediTwin services..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml down
        docker compose -f docker-compose.yml -f docker-compose.uv.yml build --no-cache
        docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d
        ;;
    "down")
        print_status "Stopping MediTwin services..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml down
        ;;
    "logs")
        SERVICE=${2:-backend}
        print_status "Showing logs for $SERVICE..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml logs -f $SERVICE
        ;;
    "test")
        print_status "Running tests in Docker environment..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml exec backend python final_implementation_test.py
        ;;
    "shell")
        print_status "Opening shell in backend container..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml exec backend /bin/bash
        ;;
    "status")
        print_status "Checking service status..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml ps
        ;;
    "clean")
        print_status "Cleaning up Docker resources..."
        docker compose -f docker-compose.yml -f docker-compose.uv.yml down -v
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {up|build|rebuild|down|logs|test|shell|status|clean} [service]"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services"
        echo "  build    - Build all images"
        echo "  rebuild  - Rebuild and restart all services"
        echo "  down     - Stop all services"
        echo "  logs     - Show logs (specify service as 2nd arg)"
        echo "  test     - Run implementation tests"
        echo "  shell    - Open shell in backend container"
        echo "  status   - Show service status"
        echo "  clean    - Clean up all resources"
        exit 1
        ;;
esac

if [ $COMMAND = "up" ] || [ $COMMAND = "rebuild" ]; then
    echo ""
    print_status "Services started! Checking health..."
    sleep 10
    
    # Check if services are running
    if docker compose -f docker-compose.yml -f docker-compose.uv.yml ps | grep -q "Up"; then
        print_status "✅ Services are running!"
        echo ""
        print_status "🔗 Access URLs:"
        echo "   Backend API: http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs" 
        echo "   MongoDB: mongodb://localhost:27017"
        echo "   Redis: localhost:6379"
        echo "   Neo4j Browser: http://localhost:7474"
        echo "   Milvus: localhost:19530"
        echo ""
        print_status "📋 Useful commands:"
        echo "   View logs: $0 logs [service]"
        echo "   Run tests: $0 test"
        echo "   Open shell: $0 shell"
        echo "   Stop services: $0 down"
    else
        print_error "❌ Some services failed to start!"
        print_status "Check logs with: $0 logs"
    fi
fi
