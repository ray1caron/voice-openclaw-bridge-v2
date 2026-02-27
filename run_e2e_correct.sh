#!/bin/bash
# Correct E2E test runner with proper PYTHONPATH

cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Set PYTHONPATH to include both src/ and project root
# This is needed because:
# - src/bridge/ contains bridge modules (audio_pipeline, websocket_client)
# - src/audio/ contains audio modules (wake_word, stt_worker, tts_worker)
export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:/home/hal/.openclaw/workspace/voice-bridge-v2:$PYTHONPATH

# Run the tests
python3 -m pytest tests/integration/test_voice_e2e.py -v --tb=short

# Exit with test result
exit $?