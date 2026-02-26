#!/bin/bash
# Start Voice Bridge in background

cd /home/hal/.openclaw/workspace/voice-bridge-v2
source ~/.voice-bridge/venv/bin/activate

# Kill any existing instance
pkill -f "python -m bridge.main" 2>/dev/null

# Start in background with logging
nohup python -m bridge.main > /tmp/voice-bridge.log 2>&1 &

sleep 2

echo "Voice Bridge started!"
echo "PID: $!"
echo "Log: tail -f /tmp/voice-bridge.log"
echo ""
echo "Say 'Hey Hal' to activate"