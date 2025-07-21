# MediTwin Backend Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Database Configuration](#database-configuration)
5. [Security Configuration](#security-configuration)
6. [Docker Deployment](#docker-deployment)
7. [Production Hardening](#production-hardening)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide covers the complete deployment process for the MediTwin Backend in production environments, including security hardening, monitoring setup, and HIPAA compliance considerations.

## Prerequisites

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 100GB+ SSD for databases
- **Network**: Stable internet connection for OpenAI API

### Software Requirements
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **SSL Certificate**: For HTTPS encryption
- **Domain Name**: For production deployment

### External Services
- **OpenAI API Key**: For LLM processing
- **Login Service**: JWT token provider (external)
- **Load Balancer**: For high availability (optional)

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/meditwin-backend.git
cd meditwin-backend
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. Configure Environment Variables
```bash
# Database Configuration
MONGO_URI=mongodb://admin:SECURE_PASSWORD@mongo:27017/meditwin?authSource=admin
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=SECURE_MONGO_PASSWORD

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=SECURE_NEO4J_PASSWORD

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379

# Milvus Configuration
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_URI=http://milvus:19530

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL_CHAT=gpt-4o-mini
OPENAI_MODEL_SEARCH=gpt-4o-mini-search-preview

# JWT Configuration (MUST MATCH LOGIN SERVICE)
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters-long
JWT_ALGORITHM=HS256
JWT_REQUIRE_AUTH=true

# Encryption Configuration
AES_ENCRYPTION_KEY=your-32-byte-aes-key-here-exactly-32-bytes
PATIENT_ID_SALT=your-patient-id-salt-for-hmac-hashing-here

# Production Settings
DEBUG=false
CORS_ORIGINS=https://your-frontend-domain.com
ALLOWED_HOSTS=your-backend-domain.com,localhost

# Optional: AgentOps for monitoring
AGENTOPS_API_KEY=your-agentops-api-key-optional
```

## Database Configuration

### MongoDB Setup
```bash
# Create MongoDB data directory
mkdir -p ./data/mongo

# Set proper permissions
chmod 777 ./data/mongo
```

### Neo4j Setup
```bash
# Create Neo4j data directory
mkdir -p ./data/neo4j

# Set proper permissions
chmod 777 ./data/neo4j
```

### Redis Setup
```bash
# Create Redis data directory
mkdir -p ./data/redis

# Set proper permissions
chmod 777 ./data/redis
```

### Milvus Setup
```bash
# Create Milvus data directories
mkdir -p ./data/milvus ./data/etcd ./data/minio

# Set proper permissions
chmod 777 ./data/milvus ./data/etcd ./data/minio
```

## Security Configuration

### 1. Docker Secrets Setup
```bash
# Create secrets directory
mkdir -p ./secrets

# Create secret files
echo "SECURE_MONGO_PASSWORD" > ./secrets/mongo_password.txt
echo "SECURE_NEO4J_PASSWORD" > ./secrets/neo4j_password.txt
echo "your-super-secret-jwt-key" > ./secrets/jwt_secret.txt
echo "your-32-byte-aes-key-here-exactly-32-bytes" > ./secrets/aes_key.txt

# Set secure permissions
chmod 600 ./secrets/*.txt
```

### 2. Update Docker Compose for Secrets
```yaml
# Add to docker-compose.yml
version: '3.8'

secrets:
  mongo_password:
    file: ./secrets/mongo_password.txt
  neo4j_password:
    file: ./secrets/neo4j_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  aes_key:
    file: ./secrets/aes_key.txt

services:
  backend:
    # ... other config
    secrets:
      - mongo_password
      - neo4j_password
      - jwt_secret
      - aes_key
```

### 3. SSL/TLS Configuration
```bash
# Create SSL certificates directory
mkdir -p ./ssl

# Copy your SSL certificates
cp /path/to/your/certificate.crt ./ssl/
cp /path/to/your/private.key ./ssl/
```

### 4. Firewall Configuration
```bash
# Ubuntu/Debian
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Block direct database access from outside
sudo ufw deny 27017/tcp  # MongoDB
sudo ufw deny 7687/tcp   # Neo4j
sudo ufw deny 6379/tcp   # Redis
sudo ufw deny 19530/tcp  # Milvus
```

## Docker Deployment

### 1. Production Docker Compose
```yaml
version: '3.8'

networks:
  meditwin_network:
    driver: bridge

volumes:
  mongo-data:
    driver: local
  redis-data:
    driver: local
  neo4j-data:
    driver: local
  milvus-data:
    driver: local
  etcd-data:
    driver: local
  minio-data:
    driver: local

services:
  # Reverse Proxy (Nginx)
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    networks:
      - meditwin_network

  # MediTwin Backend
  backend:
    build:
      context: .
      dockerfile: backend_RAG.dockerfile
    container_name: meditwin-backend
    restart: unless-stopped
    env_file: .env
    environment:
      - PYTHONPATH=/app
    depends_on:
      - mongo
      - redis
      - neo4j
      - milvus
    networks:
      - meditwin_network

  # MongoDB
  mongo:
    image: mongo:7
    container_name: mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_INITDB_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_INITDB_ROOT_PASSWORD}
    volumes:
      - mongo-data:/data/db
    networks:
      - meditwin_network

  # Redis
  redis:
    image: redis:7.0-alpine
    container_name: redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - meditwin_network

  # Neo4j
  neo4j:
    image: neo4j:5.26
    container_name: neo4j
    restart: unless-stopped
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_server_memory_heap_initial__size=1g
      - NEO4J_server_memory_heap_max__size=2g
    volumes:
      - neo4j-data:/data
    networks:
      - meditwin_network

  # Milvus Dependencies
  etcd:
    image: bitnami/etcd:3.5.9
    container_name: etcd
    environment:
      - ALLOW_NONE_AUTHENTICATION=yes
      - ETCD_ADVERTISE_CLIENT_URLS=http://0.0.0.0:2379
    volumes:
      - etcd-data:/bitnami/etcd
    networks:
      - meditwin_network

  minio:
    image: minio/minio
    container_name: minio
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
    volumes:
      - minio-data:/data
    networks:
      - meditwin_network

  # Milvus
  milvus:
    image: bitnami/milvus:2.5.13
    container_name: milvus
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
      - MINIO_ACCESS_KEY_ID=${MINIO_ROOT_USER}
      - MINIO_SECRET_ACCESS_KEY=${MINIO_ROOT_PASSWORD}
    depends_on:
      - etcd
      - minio
    volumes:
      - milvus-data:/var/lib/milvus
    networks:
      - meditwin_network
```

### 2. Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
        limit_req zone=api burst=20 nodelay;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # File upload limits
        client_max_body_size 50M;
    }
}
```

### 3. Deploy Services
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

## Production Hardening

### 1. Backend Security Configuration
Add to `src/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

# HTTPS redirect
app.add_middleware(HTTPSRedirectMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

### 2. Database Security
```bash
# MongoDB - Create admin user
docker exec -it mongo mongosh admin --eval "
db.createUser({
  user: 'admin',
  pwd: 'SECURE_PASSWORD',
  roles: [{ role: 'userAdminAnyDatabase', db: 'admin' }]
})
"

# Neo4j - Configure authentication
docker exec -it neo4j neo4j-admin set-initial-password SECURE_PASSWORD
```

### 3. System Hardening
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Monitoring & Logging

### 1. Prometheus & Grafana Setup
```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - meditwin_network

  grafana:
    image: grafana/grafana
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=SECURE_PASSWORD
    ports:
      - "3000:3000"
    networks:
      - meditwin_network
```

### 2. Log Aggregation
```bash
# Configure log rotation
sudo cat > /etc/logrotate.d/meditwin << EOF
/var/log/meditwin/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### 3. Health Checks
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
EOF

chmod +x health_check.sh

# Add to crontab
echo "*/5 * * * * /path/to/health_check.sh" | crontab -
```

## Backup & Recovery

### 1. Database Backup Scripts
```bash
# MongoDB backup
cat > backup_mongo.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="mongodb://admin:PASSWORD@localhost:27017" --out="/backup/mongo_$DATE"
tar -czf "/backup/mongo_$DATE.tar.gz" "/backup/mongo_$DATE"
rm -rf "/backup/mongo_$DATE"
EOF

# Neo4j backup
cat > backup_neo4j.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec neo4j neo4j-admin backup --backup-dir=/backup --name="neo4j_$DATE"
EOF

chmod +x backup_*.sh
```

### 2. Automated Backup Schedule
```bash
# Add to crontab
crontab -e

# Daily backups at 2 AM
0 2 * * * /path/to/backup_mongo.sh
0 2 * * * /path/to/backup_neo4j.sh
```

### 3. Disaster Recovery Plan
1. **Data Recovery**: Restore from latest backup
2. **Service Recovery**: Restart Docker services
3. **Configuration Recovery**: Restore environment files
4. **SSL Certificate Recovery**: Restore SSL certificates

## Troubleshooting

### Common Issues

1. **Backend Won't Start**
   ```bash
   # Check logs
   docker-compose logs backend
   
   # Check environment variables
   docker-compose config
   
   # Verify database connections
   docker-compose exec backend python -c "from src.db.mongo_db import get_mongo; print('MongoDB OK')"
   ```

2. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose ps
   
   # Check network connectivity
   docker-compose exec backend ping mongo
   
   # Verify credentials
   docker-compose exec mongo mongosh -u admin -p
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate validity
   openssl x509 -in ./ssl/certificate.crt -text -noout
   
   # Test SSL connection
   openssl s_client -connect your-domain.com:443
   ```

4. **Performance Issues**
   ```bash
   # Check resource usage
   docker stats
   
   # Monitor database performance
   docker exec mongo mongostat
   
   # Check API response times
   curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"
   ```

### Maintenance Tasks

1. **Regular Updates**
   ```bash
   # Pull latest images
   docker-compose pull
   
   # Update application
   docker-compose up -d --build
   ```

2. **Log Cleanup**
   ```bash
   # Clean old logs
   find /var/log/meditwin -name "*.log" -mtime +30 -delete
   
   # Clean Docker logs
   docker system prune -f
   ```

3. **Database Maintenance**
   ```bash
   # MongoDB maintenance
   docker exec mongo mongosh admin --eval "db.runCommand({compact: 'your_collection'})"
   
   # Neo4j maintenance
   docker exec neo4j neo4j-admin check-consistency
   ```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database passwords changed
- [ ] Firewall configured
- [ ] Rate limiting enabled
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Log rotation configured
- [ ] Health checks enabled
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Docker secrets implemented
- [ ] System hardening applied
- [ ] Disaster recovery plan documented

---

**Note**: This deployment involves handling sensitive medical data. Ensure compliance with healthcare regulations (HIPAA, GDPR) and follow security best practices for your specific environment.
