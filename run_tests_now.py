#!/usr/bin/env python3
"""Run E2E tests directly with Python"""
import sys
import os

# Add source to PYTHONPATH
sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2/src')
sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2')

os.chdir('/home/hal/.openclaw/workspace/voice-bridge-v2')

import subprocess

result = subprocess.run([
    sys.executable, '-m', 'pytest',
    'tests/integration/test_voice_e2e.py::TestVoiceAssistantE2E',
    '-v', '--tb=short'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)