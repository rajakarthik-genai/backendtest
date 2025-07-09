#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/tmp/meditwin-agents.log"
echo "=======================================" >> $LOG_FILE
echo "Starting agents systemd script at $(date)" >> $LOG_FILE
echo "=======================================" >> $LOG_FILE

# Function to log and execute tmux commands
send_tmux_cmd() {
    local session=$1
    local cmd=$2
    local sleep_time=${3:-1}
    
    echo "Executing: $cmd" >> $LOG_FILE
    tmux send-keys -t "$session" "$cmd" Enter
    sleep $sleep_time
}

# Kill existing session if it exists
echo "Checking for existing tmux session..." >> $LOG_FILE
if tmux has-session -t meditwin-agents 2>/dev/null; then
    echo "Killing existing session..." >> $LOG_FILE
    tmux kill-session -t meditwin-agents
fi

# Create tmux session for agents in detached mode
echo "Creating new tmux session..." >> $LOG_FILE
tmux new-session -d -s meditwin-agents
echo "Created tmux session: meditwin-agents" >> $LOG_FILE

# Navigate to project directory
send_tmux_cmd "meditwin-agents" "cd ~/agents/meditwin-agents" 2

# Activate virtual environment
send_tmux_cmd "meditwin-agents" "source .venv/bin/activate" 2

# Install/update dependencies
send_tmux_cmd "meditwin-agents" "uv pip install -r requirements.txt" 5

# Start Docker services
send_tmux_cmd "meditwin-agents" "docker compose up -d" 10

# Start ngrok tunnel
send_tmux_cmd "meditwin-agents" "ngrok http --domain=mackerel-liberal-loosely.ngrok-free.app --authtoken=2z3PqE4KmxGxjlUc3GK7omc6PO6_7HMh7qg9gw6bpDcsnbTUg 8000" 3

echo "All commands sent to tmux session" >> $LOG_FILE
echo "Agents should be available at: https://mackerel-liberal-loosely.ngrok-free.app" >> $LOG_FILE
echo "Local API: http://localhost:8000" >> $LOG_FILE
echo "TMux session: meditwin-agents" >> $LOG_FILE

# Ensure the tmux session stays alive by preventing systemd from killing it
exec sleep infinity
