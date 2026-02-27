#!/usr/bin/env python3
"""Quick validation: Check if all imports work"""
import sys
import os

sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2/src')
sys.path.insert(0, '/home/hal/.openclaw/workspace/voice-bridge-v2')

os.chdir('/home/hal/.openclaw/workspace/voice-bridge-v2')

print("Testing imports...")

try:
    from audio.wake_word import WakeWordDetector, WakeWordEvent
    print("✅ audio.wake_word imports")
except ImportError as e:
    print(f"❌ audio.wake_word: {e}")
    sys.exit(1)

try:
    from audio.stt_worker import STTWorker, TranscriptionResult
    print("✅ audio.stt_worker imports")
except ImportError as e:
    print(f"❌ audio.stt_worker: {e}")
    sys.exit(1)

try:
    from audio.tts_worker import TTSWorker
    print("✅ audio.tts_worker imports")
except ImportError as e:
    print(f"❌ audio.tts_worker: {e}")
    sys.exit(1)

try:
    from audio.barge_in import BargeInState, InterruptionEvent
    print("✅ audio.barge_in imports")
except ImportError as e:
    print(f"❌ audio.barge_in: {e}")
    sys.exit(1)

try:
    from bridge.audio_pipeline import AudioPipeline, PipelineState
    print("✅ bridge.audio_pipeline imports")
except ImportError as e:
    print(f"❌ bridge.audio_pipeline: {e}")
    sys.exit(1)

try:
    from bridge.websocket_client import OpenClawWebSocketClient, ConnectionState
    print("✅ bridge.websocket_client imports")
except ImportError as e:
    print(f"❌ bridge.websocket_client: {e}")
    sys.exit(1)

try:
    from bridge.voice_orchestrator import VoiceOrchestrator
    print("✅ bridge.voice_orchestrator imports")
except ImportError as e:
    print(f"❌ bridge.voice_orchestrator: {e}")
    sys.exit(1)

print("\n✅ All imports successful!")
print("Test infrastructure is ready.")