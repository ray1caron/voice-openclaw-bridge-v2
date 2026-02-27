#!/usr/bin/env python3
"""Run E2E tests directly"""
import subprocess
import sys
import os

os.chdir('/home/hal/.openclaw/workspace/voice-bridge-v2')
sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2/src')
sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2')

result = subprocess.run([
    'python3', '-m', 'pytest',
    'tests/integration/test_voice_e2e.py::TestVoiceAssistantE2E',
    '-v', '--tb=short'
], capture_output=True, text=True)

print(result.stdout)
print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)