#!/usr/bin/env bash
set -euo pipefail

echo "Starting agents debug script at $(date)"
cd ~/agents/meditwin-agents
echo "Changed to directory: $(pwd)"

source .venv/bin/activate
echo "Virtual environment activated"

echo "Installing requirements..."
uv pip install -r requirements.txt
echo "Requirements installed"

echo "Starting Docker containers..."
docker compose up -d &
sleep 2
echo "Docker containers started"

echo "Starting ngrok..."
# Use the specific authtoken for the agents domain
ngrok http --domain=mackerel-liberal-loosely.ngrok-free.app --authtoken=2z3PqE4KmxGxjlUc3GK7omc6PO6_7HMh7qg9gw6bpDcsnbTUg 8000 &
sleep 2
echo "Ngrok started"

echo "Keeping session alive..."
exec bash
