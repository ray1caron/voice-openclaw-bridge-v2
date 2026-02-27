#!/usr/bin/env python3
"""Fix TranscriptionResult calls in test_voice_e2e.py"""

import re

def fix_transcription_result(content):
    """Fix all TranscriptionResult calls to include required fields."""

    # Pattern 1: TranscriptionResult("text", 0.9, 100.0)
    pattern1 = r'TranscriptionResult\("([^"]+)",\s*([0-9.]+),\s*([0-9.]+)\)'
    replacement1 = lambda m: f'''TranscriptionResult(
            "{m.group(1)}",
            confidence={m.group(2)},
            language="en",
            duration_ms={m.group(3)},
            segments_count=1,
            latency_ms={m.group(3)},
        )'''
    content = re.sub(pattern1, replacement1, content)

    # Pattern 2: TranscriptionResult(text=..., confidence=..., time_ms=...)
    pattern2 = r'TranscriptionResult\(\s*text=([^,]+),\s*confidence=([^,]+),\s*time_ms=([^,\)]+)\s*\)'
    replacement2 = lambda m: f'''TranscriptionResult(
            text={m.group(1)},
            confidence={m.group(2)},
            language="en",
            duration_ms={m.group(3)},
            segments_count=1,
            latency_ms={m.group(3)},
        )'''
    content = re.sub(pattern2, replacement2, content)

    return content

if __name__ == "__main__":
    with open('tests/integration/test_voice_e2e.py', 'r') as f:
        content = f.read()

    content = fix_transcription_result(content)

    with open('tests/integration/test_voice_e2e.py', 'w') as f:
        f.write(content)

    print("✓ Fixed all TranscriptionResult calls")