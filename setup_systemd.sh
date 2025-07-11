#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up Meditwin Agents systemd service...${NC}"

# Get the current user
USER=$(whoami)

# Copy the systemd service file to the system directory
echo -e "${YELLOW}Installing systemd service file...${NC}"
sudo cp meditwin-agents-simple.service /etc/systemd/system/meditwin-agents.service

# Reload systemd to pick up the new service
echo -e "${YELLOW}Reloading systemd daemon...${NC}"
sudo systemctl daemon-reload

# Enable the service to start on boot
echo -e "${YELLOW}Enabling meditwin-agents service...${NC}"
sudo systemctl enable meditwin-agents

# Start the service now
echo -e "${YELLOW}Starting meditwin-agents service...${NC}"
sudo systemctl start meditwin-agents

# Check the status
echo -e "${GREEN}Service status:${NC}"
sudo systemctl status meditwin-agents --no-pager

echo -e "${GREEN}✓ Meditwin Agents systemd service setup complete!${NC}"
echo -e "${GREEN}✓ The service will now start automatically on boot${NC}"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:       sudo journalctl -fu meditwin-agents"
echo "  Stop service:    sudo systemctl stop meditwin-agents"
echo "  Start service:   sudo systemctl start meditwin-agents"
echo "  Restart service: sudo systemctl restart meditwin-agents"
echo "  Disable service: sudo systemctl disable meditwin-agents"
echo "  Check status:    sudo systemctl status meditwin-agents"
echo ""
echo -e "${GREEN}Your Meditwin Agents stack will be available at:${NC}"
echo "  https://mackerel-liberal-loosely.ngrok-free.app"
echo "  http://localhost:8000"
echo ""
echo -e "${YELLOW}To attach to the tmux session:${NC}"
echo "  tmux attach-session -t meditwin-agents"
