# Meditwin Agents Systemd Service Setup

This setup provides automatic startup of the Meditwin Agents stack using systemd, ensuring the service starts on boot and restarts automatically if it fails.

## Quick Start

1. **Install the service:**
   ```bash
   ./setup_systemd.sh
   ```

2. **Manage the service:**
   ```bash
   ./manage_service.sh [command]
   ```

## Files Overview

- `meditwin-agents.service` - Systemd service definition
- `setup_systemd.sh` - Installation script
- `manage_service.sh` - Service management utility
- `/home/user/scripts/start_agents.sh` - The main startup script

## Service Management Commands

### Using the management script:
```bash
./manage_service.sh start      # Start the service
./manage_service.sh stop       # Stop the service
./manage_service.sh restart    # Restart the service
./manage_service.sh status     # Show service status
./manage_service.sh logs       # Follow service logs
./manage_service.sh enable     # Enable service to start on boot
./manage_service.sh disable    # Disable service from starting on boot
./manage_service.sh tmux       # Attach to the tmux session
./manage_service.sh install    # Install/setup the systemd service
./manage_service.sh uninstall  # Remove the systemd service
```

### Using systemctl directly:
```bash
sudo systemctl start meditwin-agents@$USER
sudo systemctl stop meditwin-agents@$USER
sudo systemctl restart meditwin-agents@$USER
sudo systemctl status meditwin-agents@$USER
sudo systemctl enable meditwin-agents@$USER
sudo systemctl disable meditwin-agents@$USER
```

## Logging

View service logs:
```bash
sudo journalctl -fu meditwin-agents@$USER
```

View recent logs:
```bash
sudo journalctl -n 100 -u meditwin-agents@$USER
```

## Service Features

- **Automatic startup**: Starts on boot after network is available
- **Automatic restart**: Restarts if the service fails
- **Network dependency**: Waits for network connectivity before starting
- **Docker dependency**: Waits for Docker service to be available
- **Proper logging**: All output is captured in systemd journal
- **User isolation**: Runs under your user account

## Service Access

Once running, the service will be available at:
- **Public**: https://mackerel-liberal-loosely.ngrok-free.app
- **Local**: http://localhost:8000

## TMux Session

The service runs in a tmux session named `meditwin-agents`. You can attach to it:
```bash
tmux attach-session -t meditwin-agents
```

## Troubleshooting

### Service won't start
1. Check the service status:
   ```bash
   sudo systemctl status meditwin-agents@$USER
   ```

2. Check the logs:
   ```bash
   sudo journalctl -fu meditwin-agents@$USER
   ```

3. Verify Docker is running:
   ```bash
   sudo systemctl status docker
   ```

### Service starts but ngrok fails
1. Check if the ngrok authtoken is correct
2. Verify network connectivity
3. Check if the domain is still valid

### TMux session issues
1. List tmux sessions:
   ```bash
   tmux list-sessions
   ```

2. Kill stuck sessions:
   ```bash
   tmux kill-session -t meditwin-agents
   ```

3. Restart the service:
   ```bash
   sudo systemctl restart meditwin-agents@$USER
   ```

## Security Notes

- The ngrok authtoken is embedded in the startup script
- Consider using environment files for sensitive data
- The service runs with your user permissions
- Docker containers run with standard Docker security

## Customization

To modify the service:
1. Edit the service file: `/etc/systemd/system/meditwin-agents.service`
2. Reload systemd: `sudo systemctl daemon-reload`
3. Restart the service: `sudo systemctl restart meditwin-agents@$USER`

To modify the startup script:
1. Edit: `/home/user/scripts/start_agents.sh`
2. Restart the service: `sudo systemctl restart meditwin-agents@$USER`
