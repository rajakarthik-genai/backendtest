# MediTwin Docker Compose V2 Quick Reference

## 🚀 Essential Commands

### Start Services (UV-Optimized - Recommended)
```bash
cd deployment/
./deploy-uv.sh up
# OR manually:
docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d
```

### Start Services (Standard)
```bash
cd deployment/
docker compose up -d
```

## 🔧 Development Commands

### Build & Start Fresh
```bash
./deploy-uv.sh rebuild
# OR manually:
docker compose -f docker-compose.yml -f docker-compose.uv.yml down
docker compose -f docker-compose.yml -f docker-compose.uv.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.uv.yml up -d
```

### View Logs
```bash
# All services
./deploy-uv.sh logs

# Specific service
./deploy-uv.sh logs backend
docker compose logs -f backend

# Real-time logs for UV deployment
docker compose -f docker-compose.yml -f docker-compose.uv.yml logs -f backend
```

### Execute Commands in Container
```bash
# Open shell
./deploy-uv.sh shell
docker compose exec backend /bin/bash

# Run tests
./deploy-uv.sh test
docker compose exec backend python final_implementation_test.py

# Check API health
docker compose exec backend curl http://localhost:8000/health
```

## 📊 Monitoring & Status

### Check Service Status
```bash
./deploy-uv.sh status
docker compose ps

# Detailed status with UV
docker compose -f docker-compose.yml -f docker-compose.uv.yml ps
```

### Service Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Database connections
docker compose exec mongo mongosh --eval "db.runCommand('ping')"
docker compose exec redis redis-cli ping
docker compose exec neo4j cypher-shell -u neo4j -p your_password "RETURN 'Neo4j is running'"
```

## 🛠️ Maintenance Commands

### Stop Services
```bash
./deploy-uv.sh down
docker compose down
```

### Clean Up Everything
```bash
./deploy-uv.sh clean
# OR manually:
docker compose down -v
docker system prune -f
```

### Update & Restart
```bash
# After code changes
git pull origin main
./deploy-uv.sh rebuild

# Update specific service
docker compose build backend
docker compose up -d backend
```

## 🔍 Troubleshooting

### Check Configuration
```bash
# Validate compose files
./test-docker.sh

# Manual validation
docker compose config
docker compose -f docker-compose.yml -f docker-compose.uv.yml config
```

### Debug Service Issues
```bash
# Check logs for errors
docker compose logs backend --tail=100

# Inspect service
docker compose exec backend env
docker compose exec backend ps aux

# Network debugging
docker network ls
docker compose exec backend ping mongo
```

### Environment Issues
```bash
# Check environment variables
docker compose exec backend printenv | grep -E "(MONGO|REDIS|NEO4J|MILVUS)"

# Validate .env file
cat .env | grep -v "^#" | grep "="
```

## 📝 Quick Setup Checklist

1. ✅ **Navigate to deployment directory**: `cd deployment/`
2. ✅ **Copy environment template**: `cp .env.example .env`
3. ✅ **Edit .env with your secrets**: `nano .env`
4. ✅ **Test configuration**: `./test-docker.sh`
5. ✅ **Start services**: `./deploy-uv.sh up`
6. ✅ **Verify health**: `curl http://localhost:8000/health`
7. ✅ **Run tests**: `./deploy-uv.sh test`

## 🎯 Access Points

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017
- **Redis**: localhost:6379
- **Neo4j Browser**: http://localhost:7474
- **Milvus**: localhost:19530

---

## 💡 Pro Tips

- Use `./deploy-uv.sh` for convenience and best practices
- Always check logs when something doesn't work: `./deploy-uv.sh logs`
- UV-optimized builds are ~10x faster than standard pip builds
- The `deploy-uv.sh` script includes automatic health checks
- Use `docker compose exec` to run commands inside containers
