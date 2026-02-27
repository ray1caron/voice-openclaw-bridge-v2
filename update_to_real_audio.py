#!/usr/bin/env python3
"""
Update E2E tests to use real audio file speech_like_2s.wav

Replaces all capture_audio mocks with actual audio file data.
"""

import re

# Read the test file
with open("tests/integration/test_voice_e2e.py", "r") as f:
    content = f.read()

# Add soundfile import at the top if not present
if "import soundfile as sf" not in content:
    content = content.replace(
        "import numpy as np",
        "import numpy as np\nimport soundfile as sf"
    )

# Replace all instances of mock audio data with real audio file
old_pattern = r'orchestrator\._audio\.capture_audio = AsyncMock\(return_value=\((\d+\.?\d*), b"mock_?[a-z]*"\)\)'

def replace_with_real_audio(match):
    duration = match.group(1)
    return f'''        # Load real test audio
        audio, sr = sf.read("tests/fixtures/audio/speech_like_2s.wav")
        duration_ms = (len(audio) / sr) * 1000
        orchestrator._audio.capture_audio = AsyncMock(return_value=(duration_ms, audio.astype(np.float32)))'''

new_content = re.sub(old_pattern, replace_with_real_audio, content)

# Write back
with open("tests/integration/test_voice_e2e.py", "w") as f:
    f.write(new_content)

print("✓ Updated test file to use real audio files")
print("✓ Using speech_like_2s.wav for all audio capture mocks")