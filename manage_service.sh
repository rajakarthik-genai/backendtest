#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

USER=$(whoami)
SERVICE_NAME="meditwin-agents"

show_usage() {
    echo -e "${GREEN}Meditwin Agents Service Manager${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 [command]"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo "  start      - Start the service"
    echo "  stop       - Stop the service"
    echo "  restart    - Restart the service"
    echo "  status     - Show service status"
    echo "  logs       - Follow service logs"
    echo "  enable     - Enable service to start on boot"
    echo "  disable    - Disable service from starting on boot"
    echo "  tmux       - Attach to the tmux session"
    echo "  install    - Install/setup the systemd service"
    echo "  uninstall  - Remove the systemd service"
    echo ""
}

case "${1:-}" in
    start)
        echo -e "${YELLOW}Starting Meditwin Agents service...${NC}"
        sudo systemctl start $SERVICE_NAME
        echo -e "${GREEN}✓ Service started${NC}"
        ;;
    stop)
        echo -e "${YELLOW}Stopping Meditwin Agents service...${NC}"
        sudo systemctl stop $SERVICE_NAME
        echo -e "${GREEN}✓ Service stopped${NC}"
        ;;
    restart)
        echo -e "${YELLOW}Restarting Meditwin Agents service...${NC}"
        sudo systemctl restart $SERVICE_NAME
        echo -e "${GREEN}✓ Service restarted${NC}"
        ;;
    status)
        echo -e "${YELLOW}Service Status:${NC}"
        sudo systemctl status $SERVICE_NAME --no-pager
        ;;
    logs)
        echo -e "${YELLOW}Following service logs (Ctrl+C to exit):${NC}"
        sudo journalctl -fu $SERVICE_NAME
        ;;
    enable)
        echo -e "${YELLOW}Enabling service to start on boot...${NC}"
        sudo systemctl enable $SERVICE_NAME
        echo -e "${GREEN}✓ Service enabled${NC}"
        ;;
    disable)
        echo -e "${YELLOW}Disabling service from starting on boot...${NC}"
        sudo systemctl disable $SERVICE_NAME
        echo -e "${GREEN}✓ Service disabled${NC}"
        ;;
    tmux)
        echo -e "${YELLOW}Attaching to tmux session...${NC}"
        tmux attach-session -t meditwin-agents
        ;;
    install)
        echo -e "${YELLOW}Installing systemd service...${NC}"
        ./setup_systemd.sh
        ;;
    uninstall)
        echo -e "${YELLOW}Uninstalling systemd service...${NC}"
        sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
        sudo systemctl disable $SERVICE_NAME 2>/dev/null || true
        sudo rm -f /etc/systemd/system/meditwin-agents.service
        sudo systemctl daemon-reload
        echo -e "${GREEN}✓ Service uninstalled${NC}"
        ;;
    *)
        show_usage
        ;;
esac
