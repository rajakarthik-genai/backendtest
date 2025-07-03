#!/usr/bin/env bash
set -euo pipefail

echo "Starting systemd script at $(date)" >> /tmp/meditwin-agents.log

# Kill existing session if it exists
tmux kill-session -t meditwin-agents 2>/dev/null || true

# Create tmux session for agents in detached mode
tmux new-session -d -s meditwin-agents
echo "Created tmux session" >> /tmp/meditwin-agents.log

tmux send-keys -t meditwin-agents "cd ~/agents/meditwin-agents" Enter
sleep 1
tmux send-keys -t meditwin-agents "source .venv/bin/activate" Enter
sleep 1
tmux send-keys -t meditwin-agents "uv pip install -r requirements.txt" Enter
sleep 3
tmux send-keys -t meditwin-agents "docker compose up -d" Enter
sleep 3
tmux send-keys -t meditwin-agents "ngrok http --domain=mackerel-liberal-loosely.ngrok-free.app --authtoken=2z3PqE4KmxGxjlUc3GK7omc6PO6_7HMh7qg9gw6bpDcsnbTUg 8000" Enter
sleep 2

echo "Sent all commands to tmux session" >> /tmp/meditwin-agents.log

# Ensure the tmux session stays alive by preventing systemd from killing it
exec sleep infinity
