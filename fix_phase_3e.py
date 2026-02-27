#!/usr/bin/env python3
"""Fix Phase 3E: Dict await and None attribute issues"""

import re

with open('tests/integration/test_voice_e2e.py', 'r') as f:
    content = f.read()

# Fix 1: send_voice_input should be AsyncMock, not Mock
# The issue: send_voice_input is an async method that returns a dict
# Using Mock makes it synchronous, which causes "dict can't be used in await" errors

# Find: orchestrator._websocket = AsyncMock()
#      orchestrator._websocket.send_voice_input = Mock(return_value=mock_server.get_response())
# And change to: orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

content = re.sub(
    r'(orchestrator\._websocket = AsyncMock\(\))\s+\n+\s+(orchestrator\._websocket\.send_voice_input = )Mock\(return_value=',
    r'\1\n    \2AsyncMock(return_value=',
    content
)

# Fix 2: Ensure _wake_word is always AsyncMock before .listen is accessed
# The issue: "None does not have the attribute 'listen'"
# This means _wake_word is None somewhere

# Look for test_barge_in_during_tts and ensure _wake_word is properly set
# The test probably sets:
# orchestrator._wake_word = Mock()
# Which should be:
# orchestrator._wake_word = AsyncMock()

# Pattern:
# orchestrator._wake_word = Mock()
# ↓
# orchestrator._wake_word = AsyncMock()

content = re.sub(
    r'orchestrator\._wake_word = Mock\(\)',
    r'orchestrator._wake_word = AsyncMock()',
    content
)

with open('tests/integration/test_voice_e2e.py', 'w') as f:
    f.write(content)

print("✓ Fixed send_voice_input: Mock → AsyncMock")
print("✓ Fixed _wake_word: Mock → AsyncMock")
print("✓ This should resolve dict await and None attribute errors")