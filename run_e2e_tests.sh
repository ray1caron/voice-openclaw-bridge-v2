#!/bin/bash
# Run E2E tests with correct Python path

cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Set PYTHONPATH to include src directory
export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH

# Run the tests
python3 -m pytest tests/integration/test_voice_e2e.py -v --tb=short