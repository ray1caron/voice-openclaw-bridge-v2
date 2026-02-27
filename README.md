# Voice-OpenClaw Bridge v2

**Version:** 0.2.0
**Last Updated:** 2026-02-27
**Status:** Phase 5 Complete ✅

A bidirectional voice interface for OpenClaw AI assistant.

## Overview

Voice-OpenClaw Bridge v2 enables voice interactions with OpenClaw through a complete voice assistant pipeline:
1. **Wake Word Detection** (Porcupine) - "Computer" triggers activation
2. **Speech Capture** - Audio capture with VAD and silence detection
3. **Speech-to-Text** (Faster-Whisper) - Transcribe audio to text
4. **OpenClaw Integration** (WebSocket) - Send/receive responses
5. **Text-to-Speech** (Piper TTS) - Synthesize response to audio
6. **Audio Playback** - Play with barge-in/interruption support

**Architecture:**
```
Wake Word → Audio Capture → STT → OpenClaw → TTS → Audio Playback → [Loop]
                    ↑                                      ↓
                    └─────────── Barge-In Handler ──────────┘
```

**Key Features:**
- Complete voice interaction loop implemented
- Barge-in/interruption support during TTS playback
- Comprehensive statistics tracking
- Event callback system for monitoring
- Full test coverage (99 unit tests + 7 E2E tests)
- Python 3.10-3.12 support

---

## Phase 5 Status: COMPLETE ✅

**Completed:** 2026-02-27
**Duration:** ~60 minutes
**Progress:** 6/6 days complete (100%)

### Components Implemented:

| Component | Status | Lines | Tests |
|-----------|--------|-------|-------|
| STT Worker | ✅ Complete | 437 | 27 |
| TTS Worker | ✅ Complete | 270 | 24 |
| Wake Word Detector | ✅ Complete | 280 | 22 |
| Voice Orchestrator | ✅ Complete | 430 | 26 |
| Audio I/O | ✅ Complete | 100+ | N/A |
| E2E Tests | ✅ Complete | 500+ | 7 |
| **Total** | **✅ 100%** | **~2,017** | **106** |

### Integration Complete ✅

All 7 voice components are integrated:
- ✅ Wake Word Detector (Day 3)
- ✅ Audio Pipeline (Sprint 1)
- ✅ STT Worker (Day 1)
- ✅ WebSocket Client (Sprint 1)
- ✅ TTS Worker (Day 2)
- ✅ Audio Playback (Sprint 1)
- ✅ Barge-in Handler (Sprint 1)

---

## Hardware Requirements

| Component | Recommendation | Status |
|-----------|----------------|--------|
| **GPU** | RTX 5070 (16GB VRAM) | ✅ Optimized |
| **Microphone** | USB headset or standalone mic | Required |
| **Speakers** | Any audio output | Required |
| **CPU** | Modern multi-core | ✅ Works well |
| **RAM** | 16GB+ recommended | ✅ Sufficient |

---

## Software Stack

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `faster-whisper` | >=1.0 | Speech-to-text (Whisper) |
| `piper-tts` | >=1.2 | Text-to-speech |
| `onnxruntime` | >=1.16 | TTS inference engine |
| `numpy` | >=1.24 | Audio array processing |
| `sounddevice` | >=0.5 | Audio I/O |
| `soundfile` | >=0.12 | Audio file handling |
| `webrtcvad` | >=2.0 | Voice activity detection |
| `pvporcupine` | >=3.0 | Wake word detection |
| `pvrecorder` | >=1.2 | Audio recording for wake word |
| `websockets` | >=12.0 | WebSocket client for OpenClaw |
| `tzdata` | >=2023.3 | Timezone support (Python 3.12) |

### System Dependencies
- Python 3.10, 3.11, or 3.12
- PortAudio (for sounddevice)
- Optional: CUDA for faster whisper GPU acceleration
- Ollama (already installed)

---

## Installation

### 1. Clone Repository
```bash
cd ~/openclaw-workspace
git clone git@github.com:ray1caron/local-voice.git voice-assistant
cd voice-assistant
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install System Dependencies
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev alsa-utils
```

### 4. Install Python Dependencies
```bash
./venv/bin/pip install -r requirements.txt
```

### 5. Download Voice Model
```bash
mkdir -p voices
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json
cd ..
```

### 6. Configure Wake Word (Optional)
Edit `wakeword.py`:
- Get free access key from https://console.picovoice.ai/
- Set `WAKE_WORD = "computer"` (built-in options: computer, jarvis, alexa, hey google)

---

## Usage

### Test Wake Word
```bash
./venv/bin/python wakeword.py
# Say "computer" - should detect and exit
```

### Run Full Voice Assistant
```bash
./venv/bin/python voice.py
# Say "computer", then ask a question
```

### Example Commands
- "Computer, what time is it?"
- "Computer, tell me a joke"
- "Computer, explain quantum computing"

---

## Configuration

### Whisper Model Selection (`workers.py`)
```python
WHISPER_MODEL = "medium"  # Options: tiny, base, small, medium, large-v3
WHISPER_DEVICE = "cuda"     # "cuda" or "cpu"
WHISPER_COMPUTE_TYPE = "float16"  # "float16" or "int8"
```

### Ollama Model (`voice.py`)
```python
LLM_MODEL = "qwen2.5:14b"  # 8GB VRAM, good balance
# Alternatives: qwen2.5:7b (faster), qwen2.5:32b (higher quality)
```

### System Prompt (`voice.py`)
```python
SYSTEM_PROMPT = """
You are Hal, a helpful AI assistant. Answer concisely and naturally, 
as if speaking in conversation. Keep responses to 1-2 sentences.
"""
```

---

## Troubleshooting

### No audio devices found
```bash
# List audio devices
./venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"

# Test microphone
arecord -l
```

### CUDA out of memory
```bash
# Monitor VRAM
watch -n 1 nvidia-smi

# Reduce Whisper model size in workers.py
WHISPER_MODEL = "small"  # Uses ~2GB vs 5GB for medium
```

### Wake word not detected
- Check microphone permissions
- Verify Porcupine access key in wakeword.py
- Test with `python wakeword.py` first

### High latency
- Ensure Whisper is using CUDA (float16 mode)
- Use qwen2.5:7b instead of 14b for faster responses
- Check GPU utilization with `nvidia-smi`

---

## VRAM Budget

| Component | VRAM Usage |
|-----------|------------|
| Whisper medium | ~5GB |
| Ollama qwen2.5:14b | ~8GB |
| **Total** | **~13GB / 16GB** ✅ |

---

## Project Structure

```
voice-assistant/
├── voice.py          # Main orchestration
├── workers.py        # ASR/TTS workers  
├── wakeword.py       # Wake word detection
├── requirements.txt  # Python dependencies
├── voices/           # Piper voice models
│   └── en_US-amy-medium.onnx
├── venv/             # Virtual environment
└── README.md         # This file
```

---

## Credits

- Based on [Robin-07/local-voice](https://github.com/Robin-07/local-voice) - excellent streaming pipeline
- Ollama - local LLM execution
- Faster-Whisper - optimized Whisper inference
- Piper TTS - fast neural text-to-speech
- Porcupine - efficient wake word detection

---

## License

Fork maintains original license. Modifications by ray1caron.

## Updates

- **2026-02-26 09:13 PST**: Sprint 4 Complete - Issue #8 Barge-In/Interruption implemented with <100ms latency, 38 tests passing
- **2026-02-26**: System Test Plan created, 509 tests passing across all sprints
- **2026-02-26**: Voice Bridge v2 running on local PC (PID 10812)
- **2026-02-22**: Sprint 3 Complete - Session persistence with SQLite
- **2026-02-21**: Sprint 2 Complete - Tool chain middleware, multi-step handling
- **2026-02-20**: Sprint 1 Complete - WebSocket, audio pipeline, config system
- **2026-02-20**: Initial setup, RTX 5070 optimizations, wake word integration
