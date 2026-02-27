#!/usr/bin/env python3
"""Fix all remaining async mock issues in E2E tests"""

import re

with open('tests/integration/test_voice_e2e.py', 'r') as f:
    content = f.read()

# Fix 1: Add 'stream' parameter to all mock_tts functions
# Pattern: async def mock_tts(text):
# Replace: async def mock_tts(text, stream=True):
content = re.sub(
    r'async def mock_tts\(text\):',
    r'async def mock_tts(text, stream=True):',
    content
)

# Fix 2: Add 'stream' parameter to other tts-related functions
content = re.sub(
    r'async def interrupted_tts\(text(, stream=True)?\):',
    r'async def interrupted_tts(text, stream=True):',
    content
)

with open('tests/integration/test_voice_e2e.py', 'w') as f:
    f.write(content)

print("✓ Fixed mock_tts functions to accept 'stream' parameter")
print("✓ This should resolve 'unexpected keyword argument stream' errors")