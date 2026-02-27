# Voice-OpenClaw Bridge v2 - Installation & Setup Guide

**Version:** MVP (Phase 1)  
**Last Updated:** 2026-02-25  
**Status:** Ready for Deployment

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Dependencies & Applications](#dependencies--applications)
3. [Database Setup (SQLite)](#database-setup-sqlite)
4. [Installation Steps](#installation-steps)
5. [Configuration](#configuration)
6. [Bug Tracking System](#bug-tracking-system)
7. [Running the MVP](#running-the-mvp)
8. [OpenClaw Integration](#openclaw-integration)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores x86_64 | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Storage | 5 GB free | 10 GB (for models) |
| GPU | Optional | NVIDIA CUDA-capable |
| Audio | USB microphone + speakers | Dedicated audio interface |
| Network | Localhost only | Same subnet as OpenClaw |

**Note:** CUDA support is strongly recommended for Whisper STT performance. CPU-only mode works but latency will be higher (~2-3s vs ~500ms).

### Operating Systems

- ✅ Ubuntu 22.04+ (tested, recommended)
- ✅ Ubuntu 24.04+ (tested)
- ⚠️ Debian 12+ (should work, untested)
- ⚠️ macOS (install from source, audio device discovery different)

---

## Dependencies & Applications

### System Packages (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Core audio libraries
sudo apt-get install -y \
    portaudio19-dev \
    libsndfile1-dev \
    libportaudio2 \
    python3-dev \
    python3-pip \
    python3-venv

# Optional but recommended
sudo apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget

# For GPU support (NVIDIA only)
# Ensure CUDA drivers are installed first
# See: https://developer.nvidia.com/cuda-downloads
```

### Python Requirements

**Python Version:** 3.10, 3.11, or 3.12 (3.12 recommended)

#### Step-by-Step Installation Commands

Complete bash script to install the voice bridge:

```bash
#!/bin/bash
# Voice Bridge v2 - Complete Installation Script
# Run each section in your terminal

# ============================================
# Step 1: Verify Python version
# ============================================
python3 --version
# Should output: Python 3.10, 3.11, or 3.12

# ============================================
# Step 2: Create virtual environment
# ============================================
python3 -m venv ~/.voice-bridge/venv
cd ~/.voice-bridge/venv
source bin/activate

# Verify activation
which python3
# Should show: /home/$USER/.voice-bridge/venv/bin/python3

# ============================================
# Step 3: Upgrade pip and core tools
# ============================================
pip install --upgrade pip setuptools wheel setuptools-scm

# ============================================
# Step 4: Install core dependencies first
# ============================================
# Install dependencies individually to avoid build issues
pip install pydantic>=2.0 pyyaml>=6.0 websockets>=12.0 aiohttp>=3.9 asyncio-mqtt>=0.16

# Install audio dependencies
pip install sounddevice>=0.5 soundfile>=0.12 webrtcvad>=2.0 librosa>=0.10

# Install STT/TTS dependencies
pip install faster-whisper>=1.0 numpy>=1.24 onnxruntime>=1.16

# Install database and utilities
pip install aiosqlite>=0.19 platformdirs>=3.0 rich>=13.0 typer>=0.9 watchdog>=3.0 structlog>=23.0 python-dotenv>=1.0 pydantic-settings>=2.0

# IMPORTANT: Install tzdata for Python 3.12 (required for pydantic-settings)
# This fixes KeyError: 'zoneinfo._tzpath' when running tests
pip install tzdata>=2023.3

# Install test dependencies (optional but recommended)
pip install pytest>=7.0 pytest-asyncio>=0.21 structlog>=23.0 python-dotenv>=1.0 pydantic-settings>=2.0

# ============================================
# Step 5: Install openai-whisper (optional - may have build issues)
# ============================================
# Option A: Try with no-build-isolation (often works)
pip install openai-whisper>=20231117 --no-build-isolation || echo "Warning: openai-whisper may not be available"

# ============================================
# Step 6: Install the voice bridge package
# ============================================
cd /home/$USER/.openclaw/workspace/voice-bridge-v2
pip install -e "." --no-deps  # Skip deps since we installed them above

# ============================================
# Step 7: Verify installation
# ============================================
python3 -c "from bridge.websocket_client import WebSocketVoiceClient; print('✓ Core modules OK')"
python3 -c "from bridge.audio_pipeline import AudioPipeline; print('✓ Audio pipeline OK')"
python3 -c "from bridge.conversation_store import ConversationStore; print('✓ Conversation store OK')"
echo "Installation complete!"
```

#### Alternative: Quick Install (if you trust the environment)

```bash
# One-liner installation (assumes already in voice-bridge-v2 directory)
python3 -m venv ~/.voice-bridge/venv && \
source ~/.voice-bridge/venv/bin/activate && \
pip install --upgrade pip setuptools wheel setuptools-scm && \
pip install pydantic pyyaml websockets aiohttp sounddevice soundfile faster-whisper numpy aiosqlite platformdirs rich typer watchdog && \
pip install -e "." --no-deps && \
echo "Installation complete!"
```

### Python Package List (from pyproject.toml)

**Core Runtime:**
- `pydantic` (2.10+) - Configuration validation
- `pyyaml` (6.0+) - YAML config parsing
- `websockets` (13.0+) - WebSocket client
- `python-dotenv` (1.0+) - Environment variable loading
- `watchdog` (6.0+) - Config file monitoring (hot-reload)

**Audio Pipeline:**
- `sounddevice` (0.5+) - Audio I/O
- `soundfile` (0.13+) - Audio file handling
- `pyaudio` (0.2+) - Python audio bindings
- `numpy` (1.26+) - Numerical processing
- `webrtcvad` (2.0+) - Voice Activity Detection
- `librosa` (0.10+) - Audio analysis

**Speech Processing:**
- `faster-whisper` (1.1+) - STT engine
- `piper-tts` (1.2+) - TTS engine

**Configuration:**
- `pydantic-settings` (2.0+) - Settings management
- `python-dotenv` (1.0+) - Environment variable loading
- `structlog` (23.0+) - Structured logging

**Database:**
- `aiosqlite` (0.19+) - Async SQLite

**Testing:**
- `pytest` (7.0+) - Test framework
- `pytest-asyncio` (0.21+) - Async test support

**Python 3.12 Specific:**
- `tzdata` (2023.3+) - Timezone database (required for pydantic-settings timezone support on Python 3.12)

---

## Database Setup (SQLite)

### Overview

The voice bridge uses **SQLite** for session persistence and bug tracking. No separate database server required.

### Database Files

| Database | Location | Purpose |
|----------|----------|---------|
| Session Store | `~/.local/share/voice-bridge/sessions.db` | Conversation history |
| Bug Tracker | `~/.local/share/voice-bridge/bugs.db` | Error tracking |

### Automated Setup

Database files are **created automatically** on first run. No manual setup required.

```python
# Database initialization happens automatically
from bridge.conversation_store import ConversationStore
store = ConversationStore()  # Creates ~/.local/share/voice-bridge/sessions.db

from bridge.bug_tracker import BugTracker
tracker = BugTracker()  # Creates ~/.local/share/voice-bridge/bugs.db
```

### Manual Verification

```bash
# Check database locations
echo "Data directory: $HOME/.local/share/voice-bridge/"
ls -la ~/.local/share/voice-bridge/

# Verify SQLite works
sqlite3 ~/.local/share/voice-bridge/sessions.db ".tables"
```

### Database Schema

**sessions.db tables:**
- `sessions` - Session metadata and last activity
- `conversations` - Message history with timestamps
- `context` - OpenClaw context references

**bugs.db tables:**
- `bugs` - Bug reports with severity, status, context
- `system_state` - System info snapshots at error time
- `attachments` - Associated logs/screenshots

---

## Installation Steps

### 1. Clone Repository

```bash
# Navigate to workspace
cd /home/hal/.openclaw/workspace

# Clone the repository
git clone https://github.com/ray1caron/voice-openclaw-bridge-v2.git voice-bridge-v2
cd voice-bridge-v2
```

### 2. Install System Dependencies

```bash
# Run system check script
sudo bash scripts/install-system-deps.sh

# Or manually (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install -y portaudio19-dev libsndfile1-dev python3-dev python3-pip python3-venv
```

### 3. Create Python Environment

```bash
# Create virtual environment
python3 -m venv ~/.voice-bridge/venv

# Activate
source ~/.voice-bridge/venv/bin/activate

# Verify activation (should show path to venv)
which python3
```

### 4. Install Python Package

#### Option A: Install core dependencies first (Recommended)

This method avoids build issues with certain packages:

```bash
# Navigate to the project directory
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Activate virtual environment
source ~/.voice-bridge/venv/bin/activate

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel setuptools-scm

# Install dependencies individually
pip install pydantic>=2.0 pyyaml>=6.0 websockets>=12.0 aiohttp>=3.9 asyncio-mqtt>=0.16
pip install sounddevice>=0.5 soundfile>=0.12 webrtcvad>=2.0 librosa>=0.10
pip install faster-whisper>=1.0 numpy>=1.24 onnxruntime>=1.16
pip install aiosqlite>=0.19 platformdirs>=3.0 rich>=13.0 typer>=0.9 watchdog>=3.0

# Try installing openai-whisper (may fail - that's OK)
pip install openai-whisper>=20231117 --no-build-isolation || echo "Note: openai-whisper skipped"

# Install the bridge package without dependencies (already installed)
pip install -e "." --no-deps
```

#### Option B: Standard install (may fail on some systems)

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
source ~/.voice-bridge/venv/bin/activate
pip install --upgrade pip
pip install -e "."
```

### 5. Verify Installation

```bash
# Activate virtual environment
source ~/.voice-bridge/venv/bin/activate

# Test core imports
python3 -c "from bridge.websocket_client import WebSocketVoiceClient; print('✓ WebSocket client OK')"
python3 -c "from bridge.audio_pipeline import AudioPipeline; print('✓ Audio pipeline OK')"
python3 -c "from bridge.response_filter import ResponseFilter; print('✓ Response filter OK')"
python3 -c "from bridge.conversation_store import ConversationStore; print('✓ Conversation store OK')"

# Run tests
python3 -m pytest tests/ --tb=line -q
```

### 5. Download Models (Optional but Recommended)

```bash
# Download Whisper STT model
python scripts/download-models.py --model medium

# Download Piper TTS voice
python scripts/download-models.py --voice en_US-amy-medium
```

Model downloads (~2GB for basic setup):
- Whisper models: `~/.local/share/voice-bridge/models/whisper/`
- Piper voices: `~/.local/share/voice-bridge/models/piper/`

---

## Configuration

### Configuration Locations (XDG Compliant)

| Config Type | Path |
|-------------|------|
| Main Config | `~/.config/voice-bridge-v2/config.yaml` |
| Environment | `~/.config/voice-bridge-v2/.env` |
| Data/DB | `~/.local/share/voice-bridge/` |
| Logs | `~/.local/state/voice-bridge/logs/` |
| Cache | `~/.cache/voice-bridge/` |

### First-Time Setup Script

```bash
# Run automatic setup (recommended)
python scripts/setup.py

# This will:
# 1. Detect audio input/output devices
# 2. Create ~/.config/voice-bridge-v2/ directory
# 3. Generate config.yaml with detected devices
# 4. Create .env template
# 5. Test audio devices
```

### Manual Configuration

**Create config file:**

```bash
mkdir -p ~/.config/voice-bridge-v2
cat > ~/.config/voice-bridge-v2/config.yaml << 'EOF'
# Voice Bridge Configuration

# OpenClaw Connection
openclaw:
  host: "localhost"
  port: 3000
  secure: false
  reconnect_interval: 5
  max_reconnect_attempts: 10

# Audio Settings  
audio:
  input_device: "default"  # Use "default" or detected name
  output_device: "default"
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  
  # Voice Activity Detection
  vad:
    enabled: true
    engine: "webrtc"
    threshold: 0.5
    min_speech_duration_ms: 250
    min_silence_duration_ms: 500

# Speech-to-Text
stt:
  engine: "whisper"
  model: "base"  # Options: tiny, base, small, medium, large-v3
  device: "cpu"  # Options: cpu, cuda
  compute_type: "int8"
  language: "en"
  
# Text-to-Speech
tts:
  engine: "piper"
  model: "en_US-amy-medium"
  speed: 1.0
  volume: 0.8

# Session Management
session:
  ttl_minutes: 30
  max_history: 10
  save_path: "~/.local/share/voice-bridge/sessions"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "~/.local/state/voice-bridge/logs/bridge.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5

# Bug Tracking
bug_tracker:
  enabled: true
  auto_catch: true
  db_path: "~/.local/share/voice-bridge/bugs.db"
  github_integration: false  # Set to true + token for GitHub sync
EOF
```

### Environment Variables (.env)

```bash
cat > ~/.config/voice-bridge-v2/.env << 'EOF'
# Optional: Override config values
BRIDGE__OPENCLAW__HOST=localhost
BRIDGE__OPENCLAW__PORT=3000

# GitHub integration for bug tracking (optional)
GITHUB_TOKEN=your_token_here

# Whisper device override (optional)
WHISPER_DEVICE=cuda
EOF

# Secure the file
chmod 600 ~/.config/voice-bridge-v2/.env
```

### Audio Device Detection

```bash
# List available audio devices
python -c "
import sounddevice as sd
print('Input devices:')
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0:
        print(f'  {i}: {d[\"name\"]}')
print('\nOutput devices:')
for i, d in enumerate(sd.query_devices()):
    if d['max_output_channels'] > 0:
        print(f'  {i}: {d[\"name\"]}')
"
```

---

## Bug Tracking System

### Overview

The bug tracking system captures errors automatically with full context for debugging.

### How It Works

**Automatic Capture:**
- Uncaught exceptions are automatically logged
- System state captured at error time
- Stack traces with local variables
- Audio device status
- Memory/disk usage

**Manual Reporting:**
```python
from bridge.bug_tracker import BugTracker

tracker = BugTracker()
tracker.capture_bug(
    error="STT timeout",
    severity="MEDIUM",
    context={"audio_device": "USB Microphone"}
)
```

### CLI Tool

```bash
# View recent bugs
python -m bridge.bug_cli list

# Show specific bug
python -m bridge.bug_cli show <bug-id>

# Export bugs to JSON
python -m bridge.bug_cli export --format json --output bugs.json

# Statistics
python -m bridge.bug_cli stats
```

### Bug Severity Levels

| Level | Description | Response |
|-------|-------------|----------|
| CRITICAL | Audio pipeline crash | Immediate restart |
| HIGH | WebSocket disconnect | Reconnect attempt |
| MEDIUM | STT accuracy drop | Log and continue |
| LOW | Minor UI glitch | Log only |

### Database Schema

```sql
-- View bug table schema
sqlite3 ~/.local/share/voice-bridge/bugs.db ".schema bugs"

-- List recent bugs
sqlite3 ~/.local/share/voice-bridge/bugs.db \
  "SELECT id, timestamp, severity, status, error_type FROM bugs ORDER BY timestamp DESC LIMIT 10;"
```

### GitHub Integration (Optional)

To sync bugs to GitHub:

```python
# config.yaml
bug_tracker:
  github_integration: true
  github_repo: "ray1caron/voice-openclaw-bridge-v2"
```

```bash
# Set token in .env
echo "GITHUB_TOKEN=ghp_xxxxxxxx" >> ~/.config/voice-bridge-v2/.env
```

---

## Running the MVP

### Quick Start

```bash
# 1. Ensure OpenClaw is running
# OpenClaw should be running on localhost:3000

# 2. Activate environment
source ~/.voice-bridge/venv/bin/activate
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# 3. Run first-time setup (if not done)
python scripts/setup.py

# 4. Start the bridge
python -m bridge.main

# Or use the run script
./run_bridge.sh
```

### Running with Different Modes

```bash
# Development mode (verbose logging)
python -m bridge.main --debug

# Push-to-talk mode (MVP default)
python -m bridge.main --mode ptt

# Headless mode (no audio feedback)
python -m bridge.main --headless

# With custom config
python -m bridge.main --config /path/to/custom-config.yaml
```

### Systemd Service (User-Level - Recommended)

**⚠️ Important:** Run first-time setup manually BEFORE starting the systemd service:

```bash
# FIRST: Do initial setup to configure audio devices
source ~/.voice-bridge/venv/bin/activate
cd /home/hal/.openclaw/workspace/voice-bridge-v2
python -m bridge.main
# This will discover audio devices and create config file

# THEN: Start systemd service
systemctl --user daemon-reload
systemctl --user enable voice-bridge
systemctl --user start voice-bridge
systemctl --user status voice-bridge
```

**Service is already created at:** `~/.config/systemd/user/voice-bridge.service`

```bash
# Reload systemd daemon
systemctl --user daemon-reload

# Enable service (auto-start on login)
systemctl --user enable voice-bridge

# Start service now
systemctl --user start voice-bridge

# Check status
systemctl --user status voice-bridge

# View logs
journalctl --user -u voice-bridge -f

# Stop service
systemctl --user stop voice-bridge

# Disable auto-start
systemctl --user disable voice-bridge
```

**Service Features:**
- Auto-starts after network is online
- Waits for OpenClaw gateway
- Restarts on failure (max 3 attempts/minute)
- Logs to journald
- User-level (no sudo required)
- Security sandboxing enabled

### Systemd Service (System-Level)

For system-wide service (requires sudo):

```bash
# Copy service file to system location
sudo cp ~/.config/systemd/user/voice-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-bridge
sudo systemctl start voice-bridge
```

---

## OpenClaw Integration

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                           │
│  │  User Speech │                                           │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐     ┌──────────────┐                     │
│  │  STT Engine  │────▶│ WebSocket    │                     │
│  │  (Whisper)   │     │ Client       │                     │
│  └──────────────┘     └──────┬───────┘                     │
│                              │                             │
│                              │ POST /api/voice/chat        │
│                              │ (voice_mode=true)           │
│                              ▼                             │
│  ┌──────────────────────────────────────┐                   │
│  │           OPENCLAW GATEWAY          │                   │
│  │  ┌──────────┐    ┌──────────────┐  │                   │
│  │  │  Agent   │───▶│  Tool Engine  │  │                   │
│  │  │  (LLM)   │◀───│  (Web Search, │  │                   │
│  │  └────┬─────┘    │   Files, etc) │  │                   │
│  │       │          └──────────────┘  │                   │
│  │       │                              │                   │
│  │       │ Final response only         │                   │
│  │       ▼                              │                   │
│  │  ┌──────────────┐                    │                   │
│  │  │   Response   │  (filtered)        │                   │
│  │  │   Filter     │◀───────────────────┘                   │
│  │  └──────┬───────┘                                       │
│  └─────────┼─────────────────────────────┘                  │
│            │                                                │
│            │ WebSocket SSE                                   │
│            │ {"type": "final", "content": "..."}           │
│            ▼                                                │
│  ┌──────────────┐                                           │
│  │     TTS      │                                           │
│  │   (Piper)    │                                           │
│  └──────┬────────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                           │
│  │ Speakers     │                                           │
│  └──────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### OpenClaw Configuration

The bridge connects to OpenClaw's built-in voice endpoints:

**HTTP Endpoint (MVP):**
- `POST http://localhost:3000/api/voice/chat`
- Header: `X-Voice-Mode: true`
- Body: `{"message": "...", "session_id": "..."}`

**WebSocket Endpoint (v2.5):**
- `ws://localhost:3000/voice`
- Bidirectional streaming

### Response Filtering

Only `type: "final"` messages trigger TTS:

```json
// Filtered out (not spoken):
{"type": "thinking", "content": "Let me search..."}
{"type": "tool_call", "tool": "web_search", "parameters": {...}}
{"type": "tool_result", "content": "..."}

// Spoken:
{"type": "final", "content": "It's 72°F and sunny today."}
```

### Session Linking

Voice sessions are linked to OpenClaw sessions:

```python
# Bridge creates voice session
voice_session = session_manager.create_session()

# Links to OpenClaw session on first message
openclaw_session_id = bridge_client.get_session_id()
voice_session.link_openclaw_session(openclaw_session_id)

# Context persists across turns
```

---

## Troubleshooting

### Audio Issues

**No audio input detected:**
```bash
# Check PulseAudio
pactl list sources | grep -A5 "Name:"

# Test microphone
arecord -d 5 -f cd test.wav && aplay test.wav

# Check permissions
sudo usermod -aG audio $USER  # Log out/in after
```

**"PortAudio not found":**
```bash
sudo apt-get install portaudio19-dev libportaudio2
pip install --force-reinstall sounddevice
```

### STT Issues

**Whisper model download fails:**
```bash
# Manual download
mkdir -p ~/.local/share/voice-bridge/models/whisper
cd ~/.local/share/voice-bridge/models/whisper

# Download from Hugging Face
wget https://huggingface.co/Systran/faster-whisper-medium/resolve/main/model.bin
```

**CUDA not detected:**
```bash
# Check CUDA
nvidia-smi

# Install torch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Connection Issues

**"Cannot connect to OpenClaw":**
```bash
# Verify OpenClaw is running
curl http://localhost:3000/health

# Check OpenClaw logs
journalctl -u openclaw -n 50
```

### Database Issues

**"Database is locked":**
```bash
# Kill any hanging processes
fuser ~/.local/share/voice-bridge/sessions.db

# Reset databases (WARNING: loses history)
rm ~/.local/share/voice-bridge/*.db
```

---

## Quick Reference

### Commands Summary

```bash
# Setup
sudo apt-get install portaudio19-dev libsndfile1-dev python3-venv
python3 -m venv ~/.voice-bridge/venv
source ~/.voice-bridge/venv/bin/activate
pip install -e "."
python scripts/setup.py

# Run
python -m bridge.main

# Test
python -m pytest tests/ --tb=line -q

# Logs
tail -f ~/.local/state/voice-bridge/logs/bridge.log

# Bugs
python -m bridge.bug_cli list

# Config
nano ~/.config/voice-bridge-v2/config.yaml
```

### File Locations

| What | Where |
|------|-------|
| Config | `~/.config/voice-bridge-v2/config.yaml` |
| Databases | `~/.local/share/voice-bridge/*.db` |
| Models | `~/.local/share/voice-bridge/models/` |
| Logs | `~/.local/state/voice-bridge/logs/` |
| Cache | `~/.cache/voice-bridge/` |

---

## Support

- **GitHub Issues:** https://github.com/ray1caron/voice-openclaw-bridge-v2/issues
- **Documentation:** See `docs/` directory in repository
- **Test Status:** Run `python -m pytest tests/ -v`

---

**Ready to run?** Start with:

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
source ~/.voice-bridge/venv/bin/activate
python -m bridge.main
```