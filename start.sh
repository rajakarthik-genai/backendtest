# ~/agents/meditwin-agents/start.sh
#!/usr/bin/env bash
cd ~/agents/meditwin-agents
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
sleep 2
ngrok http --domain=mackerel-liberal-loosely.ngrok-free.app 8000
exec bash
