#!/bin/bash
# Quick test script for voice-bridge-v2

cd /home/hal/.openclaw/workspace/voice-bridge-v2
source ~/.voice-bridge/venv/bin/activate

# Add src to Python path
export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH

# Test imports
echo "Testing imports..."
python3 -c "from bridge import __version__; print(f'✓ Bridge version: {__version__}')"
python3 -c "from bridge.websocket_client import WebSocketVoiceClient; print('✓ WebSocket client OK')"
python3 -c "from bridge.audio_pipeline import AudioPipeline; print('✓ Audio pipeline OK')"
python3 -c "from bridge.conversation_store import ConversationStore; print('✓ Conversation store OK')"

echo ""
echo "All imports successful!"
echo "Running tests..."

# Run tests
python3 -m pytest tests/ --tb=line -q
