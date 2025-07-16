# Deployment Directory

This directory contains all deployment-related configurations and scripts.

## Files

- `docker-compose.yml` - Docker Compose configuration for multi-container deployment
- `backend_RAG.dockerfile` - Docker image configuration for the backend service
- `meditwin-agents.service` - Systemd service configuration
- `meditwin-agents-simple.service` - Simplified systemd service configuration
- `start.sh` - Startup script for the application

## Deployment Options

### Docker Deployment

Use Docker Compose for easy deployment:

```bash
cd deployment
docker-compose up -d
```

### Systemd Service

For production deployment with systemd:

1. Copy the service file:
```bash
sudo cp meditwin-agents.service /etc/systemd/system/
```

2. Enable and start the service:
```bash
sudo systemctl enable meditwin-agents
sudo systemctl start meditwin-agents
```

### Manual Deployment

Use the startup script for manual deployment:

```bash
./deployment/start.sh
```

## Configuration

Make sure to:
1. Configure environment variables (`.env` file)
2. Set up required databases
3. Configure network settings
4. Set appropriate file permissions

See the main [Deployment Guide](../docs/DEPLOYMENT.md) for detailed instructions.
