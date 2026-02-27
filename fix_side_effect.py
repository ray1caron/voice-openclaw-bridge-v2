#!/usr/bin/env python3
"""Fix AsyncMock return_value to side_effect for send_voice_input"""

import re

with open('tests/integration/test_voice_e2e.py', 'r') as f:
    content = f.read()

# Issue: AsyncMock(return_value=...) returns a coroutine, not the actual value
# Solution: Use AsyncMock(side_effect=lambda x: ...) to ensure we return the dict

# Pattern 1: orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())
# We need to change this to use side_effect with a lambda to bypass the async wrapper

# Find all instances and fix them
count = 0
lines = content.split('\n')
new_lines = []

for i, line in enumerate(lines):
    if 'send_voice_input = AsyncMock(return_value=mock_server.get_response())' in line:
        # Replace with side_effect
        new_line = line.replace(
            'AsyncMock(return_value=mock_server.get_response())',
            'AsyncMock(side_effect=lambda text: mock_server.get_response())'
        )
        new_lines.append(new_line)
        count += 1
        print(f"Line {i+1}: Fixed")
    else:
        new_lines.append(line)

if count > 0:
    with open('tests/integration/test_voice_e2e.py', 'w') as f:
        f.write('\n'.join(new_lines))
    print(f"\n✓ Fixed {count} occurrences of send_voice_input AsyncMock return_value")
    print("✓ Changed to side_effect to return dict directly")
else:
    print("No occurrences found")

# Also fix any _wake_word = Mock() that might still exist
content = '\n'.join(new_lines)
if 'orchestrator._wake_word = Mock()' in content:
    content = content.replace('orchestrator._wake_word = Mock()', 'orchestrator._wake_word = AsyncMock()')
    print("✓ Fixed _wake_word Mock → AsyncMock")
    with open('tests/integration/test_voice_e2e.py', 'w') as f:
        f.write(content)