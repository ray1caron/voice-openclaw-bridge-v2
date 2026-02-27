#!/bin/bash
# Run E2E tests with correct PYTHONPATH

cd /home/hal/.openclaw/workspace/voice-bridge-v2

export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:/home/hal/.openclaw/workspace/voice-bridge-v2:$PYTHONPATH

echo "=== Running E2E Tests ==="
python3 -m pytest tests/integration/test_voice_e2e.py -v --tb=short

exit $?