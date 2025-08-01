# Deployment Guide

This guide covers deployment strategies for the MediTwin system across different environments.

## 🏗️ Deployment Overview

MediTwin supports multiple deployment strategies:
- **Local Development**: Docker Compose for development
- **Production**: Kubernetes or Docker Swarm
- **Cloud**: AWS, GCP, Azure with managed services
- **Hybrid**: On-premises with cloud backup

## 🐳 Docker Deployment

### Development Environment

#### Docker Compose Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
    depends_on:
      - mongodb
      - neo4j
      - redis
      - milvus
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs

  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  milvus:
    image: milvusdb/milvus:latest
    ports:
      - "19530:19530"
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    depends_on:
      - etcd
      - minio

volumes:
  mongodb_data:
  neo4j_data:
  redis_data:
  milvus_data:
```

#### Running Development Environment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3

# Stop all services
docker-compose down
```

### Production Environment

#### Production Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    env_file:
      - .env.prod
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js
    restart: unless-stopped

  neo4j:
    image: neo4j:5-enterprise
    environment:
      NEO4J_AUTH: ${NEO4J_USERNAME}/${NEO4J_PASSWORD}
      NEO4J_ACCEPT_LICENSE_AGREEMENT: yes
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped

volumes:
  mongodb_data:
    driver: local
  neo4j_data:
    driver: local
  neo4j_logs:
    driver: local
```

## ☸️ Kubernetes Deployment

### Kubernetes Manifests

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: meditwin
  labels:
    name: meditwin
```

#### ConfigMap
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: meditwin-config
  namespace: meditwin
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
```

#### Secrets
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: meditwin-secrets
  namespace: meditwin
type: Opaque
data:
  jwt-secret: <base64-encoded-secret>
  mongodb-password: <base64-encoded-password>
  neo4j-password: <base64-encoded-password>
  openai-api-key: <base64-encoded-key>
```

#### API Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: meditwin-api
  namespace: meditwin
spec:
  replicas: 3
  selector:
    matchLabels:
      app: meditwin-api
  template:
    metadata:
      labels:
        app: meditwin-api
    spec:
      containers:
      - name: api
        image: meditwin/api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: meditwin-config
        - secretRef:
            name: meditwin-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

#### Service
```yaml
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: meditwin-api-service
  namespace: meditwin
spec:
  selector:
    app: meditwin-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: meditwin-ingress
  namespace: meditwin
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.meditwin.com
    secretName: meditwin-tls
  rules:
  - host: api.meditwin.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: meditwin-api-service
            port:
              number: 80
```

### Database StatefulSets

#### MongoDB StatefulSet
```yaml
# k8s/mongodb-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: meditwin
spec:
  serviceName: mongodb-service
  replicas: 3
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:7
        ports:
        - containerPort: 27017
        envFrom:
        - secretRef:
            name: mongodb-secrets
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

### Deployment Commands
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n meditwin

# View logs
kubectl logs -f deployment/meditwin-api -n meditwin

# Scale deployment
kubectl scale deployment meditwin-api --replicas=5 -n meditwin

# Update deployment
kubectl set image deployment/meditwin-api api=meditwin/api:v2.0.0 -n meditwin
```

## ☁️ Cloud Deployment

### AWS Deployment

#### EKS Cluster Setup
```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create EKS cluster
eksctl create cluster \
  --name meditwin-cluster \
  --version 1.28 \
  --region us-west-2 \
  --nodegroup-name linux-nodes \
  --node-type m5.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed
```

#### RDS for MongoDB Alternative
```yaml
# terraform/rds.tf
resource "aws_db_instance" "meditwin_postgres" {
  identifier             = "meditwin-postgres"
  engine                 = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.t3.medium"
  allocated_storage     = 100
  storage_encrypted     = true
  
  db_name  = "meditwin"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "meditwin-final-snapshot"
  
  tags = {
    Name = "MediTwin Database"
    Environment = "production"
  }
}
```

#### ElastiCache for Redis
```yaml
# terraform/elasticache.tf
resource "aws_elasticache_subnet_group" "main" {
  name       = "meditwin-cache-subnet"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "meditwin-redis"
  description                  = "Redis cluster for MediTwin"
  
  node_type                   = "cache.t3.micro"
  port                        = 6379
  parameter_group_name        = "default.redis7"
  
  num_cache_clusters          = 2
  automatic_failover_enabled  = true
  multi_az_enabled           = true
  
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "MediTwin Redis"
    Environment = "production"
  }
}
```

### GCP Deployment

#### GKE Cluster
```bash
# Create GKE cluster
gcloud container clusters create meditwin-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade
```

#### Cloud SQL
```yaml
# terraform/cloudsql.tf
resource "google_sql_database_instance" "main" {
  name             = "meditwin-postgres"
  database_version = "POSTGRES_15"
  region          = "us-central1"
  
  settings {
    tier = "db-f1-micro"
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_network
    }
    
    backup_configuration {
      enabled                        = true
      start_time                    = "03:00"
      location                      = "us"
      point_in_time_recovery_enabled = true
    }
    
    database_flags {
      name  = "log_statement"
      value = "all"
    }
  }
  
  deletion_protection = true
}
```

### Azure Deployment

#### AKS Cluster
```bash
# Create resource group
az group create --name MediTwin --location eastus

# Create AKS cluster
az aks create \
  --resource-group MediTwin \
  --name meditwin-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys
```

## 🔒 Security Configuration

### SSL/TLS Configuration

#### Nginx SSL Configuration
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.meditwin.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables Security

#### Production Environment File
```bash
# .env.prod
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database URLs (use managed services in production)
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/meditwin
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
REDIS_URL=rediss://user:pass@redis-cluster.com:6380

# Security
JWT_SECRET_KEY=<strong-random-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=8

# External APIs
OPENAI_API_KEY=<production-api-key>

# Monitoring
SENTRY_DSN=<sentry-dsn>
LOG_LEVEL=INFO
```

### Network Security

#### Security Groups (AWS)
```yaml
# terraform/security-groups.tf
resource "aws_security_group" "api" {
  name_prefix = "meditwin-api"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "MediTwin API Security Group"
  }
}
```

## 📊 Monitoring & Logging

### Prometheus Monitoring
```yaml
# k8s/prometheus.yaml
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: meditwin-api
  namespace: meditwin
spec:
  selector:
    matchLabels:
      app: meditwin-api
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "MediTwin Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])"
          }
        ]
      }
    ]
  }
}
```

### Log Aggregation
```yaml
# k8s/fluentd.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: meditwin
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd:v1.16-debian-1
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
```

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install UV
      run: pip install uv
    
    - name: Install dependencies
      run: uv sync
    
    - name: Run tests
      run: uv run pytest
    
    - name: Run health checks
      run: uv run python tests/test_health_check.py

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t meditwin/api:${{ github.sha }} .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push meditwin/api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/meditwin-api api=meditwin/api:${{ github.sha }} -n meditwin
        kubectl rollout status deployment/meditwin-api -n meditwin
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Environment variables configured
- [ ] SSL certificates obtained
- [ ] Database backups created
- [ ] Security groups configured
- [ ] Monitoring setup
- [ ] Health checks working
- [ ] Load testing completed

### Deployment
- [ ] Deploy database migrations
- [ ] Deploy application
- [ ] Verify health endpoints
- [ ] Test critical user flows
- [ ] Monitor error rates
- [ ] Check performance metrics

### Post-Deployment
- [ ] Verify all services healthy
- [ ] Check log aggregation
- [ ] Validate monitoring alerts
- [ ] Test backup procedures
- [ ] Document any issues
- [ ] Update runbook

## 🆘 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it deployment/meditwin-api -n meditwin -- python -c "from src.db.mongodb import get_database; import asyncio; print('DB OK' if asyncio.run(get_database()) else 'DB FAIL')"
```

#### SSL Certificate Issues
```bash
# Check certificate expiry
openssl x509 -in cert.pem -text -noout | grep "Not After"

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

#### Performance Issues
```bash
# Check resource usage
kubectl top pods -n meditwin

# Scale up if needed
kubectl scale deployment meditwin-api --replicas=10 -n meditwin
```

### Emergency Procedures

#### Rollback Deployment
```bash
# Rollback to previous version
kubectl rollout undo deployment/meditwin-api -n meditwin

# Check rollback status
kubectl rollout status deployment/meditwin-api -n meditwin
```

#### Database Recovery
```bash
# Restore from backup
mongorestore --uri="mongodb://localhost:27017" --archive=backup.archive

# Verify data integrity
python scripts/verify_data_integrity.py
```

Remember: Always test deployment procedures in staging before production!
