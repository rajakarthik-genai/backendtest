#!/usr/bin/env bash
set -euo pipefail

# Check if already running in tmux
if [ -z "${TMUX:-}" ]; then
    # Not in tmux, create new session
    exec tmux new-session -d -s meditwin-agents "$0" \; attach-session -t meditwin-agents
fi

# Now we're inside tmux
cd ~/agents/meditwin-agents

source .venv/bin/activate
uv pip install -r requirements.txt

# Start Docker containers in background
docker compose up -d
echo "Waiting for services to start..."
sleep 10

# Wait for backend service to be healthy
echo "Checking backend service health..."
while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
    echo "Waiting for backend service to be ready..."
    sleep 5
done
echo "Backend service is ready!"

# Use the specific authtoken for the agents domain
ngrok http --domain=mackerel-liberal-loosely.ngrok-free.app --authtoken=2z3PqE4KmxGxjlUc3GK7omc6PO6_7HMh7qg9gw6bpDcsnbTUg 8000 &
sleep 2

echo "Meditwin Agents stack is running in tmux session 'meditwin-agents'"
echo "Docker containers, FastAPI server, and ngrok tunnel are active"
echo "FastAPI server: http://localhost:8000"
echo "Ngrok tunnel: https://mackerel-liberal-loosely.ngrok-free.app"
exec bash                                    # keep tmux window open
