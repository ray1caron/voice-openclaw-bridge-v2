#!/usr/bin/env python3
"""Quick import test for STT worker."""

import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Testing imports...")

try:
    from audio.stt_worker import STTWorker, TranscriptionResult, STTStats
    print("✅ STT worker imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

try:
    # Check if faster-whisper is available
    import faster_whisper
    print(f"✅ faster-whisper available: {faster_whisper.__version__ if hasattr(faster_whisper, '__version__') else 'unknown'}")
except ImportError:
    print("⚠️  faster-whisper not installed (this is OK for unit tests with mocks)")

try:
    import numpy
    print(f"✅ numpy available: {numpy.__version__}")
except ImportError:
    print("❌ numpy not installed")
    sys.exit(1)

print("\n✅ All critical imports successful!")