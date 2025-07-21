# MediTwin Docker Deployment Guide

This directory contains all deployment-related configurations and scripts with optimized Docker support using `uv`.

## 📦 Files Overview

- `docker-compose.yml` - Main Docker Compose configuration
- `docker-compose.uv.yml` - UV-optimized override for faster builds
- `backend_RAG.dockerfile` - Standard Docker image (pip-based)
- `backend_RAG_uv.dockerfile` - UV-optimized Docker image (recommended)
- `deploy-uv.sh` - Convenient deployment script with UV support
- `meditwin-agents.service` - Systemd service configuration
- `start.sh` - Startup script for the application

## 🚀 Quick Start (UV-Optimized)

The fastest way to deploy using `uv`:

```bash
cd deployment/
./deploy-uv.sh up
```

## 📋 Deployment Options

### 1. UV-Optimized Docker (Recommended)

Use UV for faster dependency management:

```bash
cd deployment/
./deploy-uv.sh up
```

### 2. Standard Docker Deployment

Use standard Docker Compose:

```bash
cd deployment/
docker compose up -d
```

### 3. Systemd Service

For production deployment with systemd:

1. Copy the service file:
```bash
sudo cp meditwin-agents.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable meditwin-agents
sudo systemctl start meditwin-agents
```

2. Check status:
```bash
sudo systemctl status meditwin-agents
```

### 4. Manual Deployment

Use the startup script for manual deployment:

```bash
./deployment/start.sh
```

## 🛠️ Docker Compose Commands

### UV-Optimized Deployment (Recommended):
```bash
# Start all services
docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d

# Build from scratch
docker compose -f docker-compose.yml -f docker-compose.uv.yml build --no-cache

# View logs
docker compose -f docker-compose.yml -f docker-compose.uv.yml logs -f backend

# Stop services
docker compose -f docker-compose.yml -f docker-compose.uv.yml down
```

### Standard Deployment:
```bash
# Start all services
docker compose up -d

# Build specific service
docker compose build backend

# View specific service logs
docker compose logs -f backend

# Execute commands in running container
docker compose exec backend python final_implementation_test.py

# Stop services
docker compose down
```

## 📊 Service Health Monitoring

Check service status:
```bash
# All services
docker compose ps

# Specific service health
docker compose exec backend curl http://localhost:8000/health
```

## 🔧 Development Mode

For development with live code reloading:
```bash
# Use UV override with source mounting
docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d

# Watch logs in real-time
docker compose -f docker-compose.yml -f docker-compose.uv.yml logs -f backend
```
