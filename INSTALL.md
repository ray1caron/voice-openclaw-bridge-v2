# Voice-OpenClaw Bridge v2 - Installation Guide

**Version:** 1.0.0-beta
**Last Updated:** 2026-02-28
**Status:** Production Ready ✅

---

## Quick Installation

```bash
# Clone and install
git clone --branch v1.0.0-beta https://github.com/ray1caron/voice-openclaw-bridge-v2.git
cd voice-openclaw-bridge-v2
pip install -e .

# Run setup wizard
python3 -m bridge.main setup

# Install systemd service
sudo ./scripts/install.sh

# Start service
sudo systemctl start voice-bridge.service
```

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Dependencies & Applications](#dependencies--applications)
3. [Production Installation](#production-installation)
4. [Configuration](#configuration)
5. [Systemd Service](#systemd-service)
6. [Installation Scripts](#installation-scripts)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores (x86_64) | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Storage** | 500 MB | 1 GB |
| **GPU** | None | NVIDIA CUDA (optional) |
| **Microphone** | USB mic | USB headset |
| **Speakers** | Any | Any audio output |
| **Network** | Low latency | Wired network |

### Operating Systems

- ✅ **Ubuntu 22.04+** (tested, recommended)
- ✅ **Ubuntu 24.04+** (tested)
- ⚠️ Debian 12+ (should work, untested)
- ⚠️ macOS (install from source, audio device discovery differs)

### Python Version

**Required:** Python 3.10, 3.11, or 3.12

```bash
# Check Python version
python3 --version  # Should be 3.10, 3.11, or 3.12
```

---

## Dependencies & Applications

### System Packages (Ubuntu/Debian)

```bash
# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    portaudio19-dev \
    libsndfile1-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    ffmpeg
```

### Optional: GPU Support

If you have an NVIDIA GPU, install CUDA drivers for faster STT:

```bash
# Install NVIDIA drivers
sudo apt-get install -y \
    nvidia-driver-535 \
    nvidia-cuda-toolkit
```

---

## Production Installation

### Step 1: Clone Repository

```bash
# Clone v1.0.0-beta release
git clone --branch v1.0.0-beta https://github.com/ray1caron/voice-openclaw-bridge-v2.git
cd voice-openclaw-bridge-v2
```

### Step 2: Install Python Dependencies

```bash
# Install package in development mode
pip install -e .

# Or install with extras for development
pip install -e ".[dev]"
```

**Dependencies:** (installed automatically)
- `pydantic` - Configuration management
- `websockets` - OpenClaw WebSocket client
- `numpy` - Audio processing
- `soundfile` - Audio file I/O
- `faster-whisper` - Speech-to-Text
- `piper-tts` - Text-to-Speech
- `pvporcupine` - Wake word detection
- `structlog` - Logging

### Step 3: Run Setup Wizard

```bash
# Interactive setup wizard
python3 -m bridge.main setup
```

The setup wizard will:
1. Detect available audio devices
2. Create configuration file
3. Setup data directories
4. Test audio I/O
5. Configure OpenClaw connection

**Setup Locations:**
- **Config:** `~/.config/voice-bridge/config.yaml`
- **Data:** `~/.local/share/voice-bridge/`

### Step 4: Install Systemd Service

```bash
# Run installation script
sudo ./scripts/install.sh
```

This script will:
- Copy `voice-bridge.service` to `/etc/systemd/system/`
- Reload systemd daemon
- Enable service at boot

### Step 5: Start Service

```bash
# Start the service
sudo systemctl start voice-bridge.service

# Check status
sudo systemctl status voice-bridge.service

# View logs (Ctrl+C to exit)
journalctl -u voice-bridge.service -f
```

---

## Configuration

### Configuration File

**Location:** `~/.config/voice-bridge/config.yaml`

### Audio Configuration

```yaml
audio:
  input_device: "default"  # Audio input device
  output_device: "default"  # Audio output device
  sample_rate: 16000
  channels: 1
  chunk_size: 1024
  buffer_size: 4096
```

### OpenClaw Configuration

```yaml
openclaw:
  backend_url: "ws://localhost:8765"
  session_id: "voice-session"
  timeout: 30
  reconnect_delay: 1
  max_reconnect_delay: 30
```

### STT Configuration

```yaml
stt:
  model_size: "small"  # Choices: tiny, base, small, medium, large
  device: "auto"  # cpu or cuda if available
  language: "en"
  compute_type: "float16"
```

### TTS Configuration

```yaml
tts:
  model: "en_US-amy-medium"  # Piper TTS model
  sample_rate: 22050
  buffer_size: 512
```

### Wake Word Configuration

```yaml
wake_word:
  keyword: "computer"  # Porcupine wake word
  sensitivity: 0.5
  access_key: ""  # Get from Picovoice (free)
```

Rerun setup wizard to reconfigure:
```bash
python3 -m bridge.main setup
```

---

## Systemd Service

### Service Management

```bash
# Start service
sudo systemctl start voice-bridge.service

# Stop service
sudo systemctl stop voice-bridge.service

# Restart service
sudo systemctl restart voice-bridge.service

# Enable at boot
sudo systemctl enable voice-bridge.service

# Disable at boot
sudo systemctl disable voice-bridge.service

# View status
sudo systemctl status voice-bridge.service

# View logs (live follow)
journalctl -u voice-bridge.service -f

# View last 100 lines of logs
journalctl -u voice-bridge.service -n 100
```

### Service File

The systemd service is installed at `/etc/systemd/system/voice-bridge.service`:

```ini
[Unit]
Description=Voice-OpenClaw Bridge v2 Service
After=network.target sound.target openclaw.service

[Service]
Type=simple
User=hal
WorkingDirectory=/home/hal/.openclaw/workspace/voice-bridge-v2
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 -m bridge.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Installation Scripts

### scripts/install.sh

Install systemd service and enable on boot.

```bash
sudo ./scripts/install.sh
```

### scripts/manage_service.sh

Manage the voice-bridge service.

```bash
# Start
sudo ./scripts/manage_service.sh start

# Stop
sudo ./scripts/manage_service.sh stop

# Restart
sudo ./scripts/manage_service.sh restart

# Status
sudo ./scripts/manage_service.sh status

# Logs
sudo ./scripts/manage_service.sh logs
```

### scripts/uninstall.sh

Uninstall systemd service.

```bash
sudo ./scripts/uninstall.sh
```

---

## Environment Variables

Optional environment variables:

```bash
# OpenClaw backend URL
export VOICE_BRIDGE_BACKEND_URL="ws://localhost:8765"

# Session ID
export VOICE_BRIDGE_SESSION_ID="voice-session"

# Config file location
export VOICE_BRIDGE_CONFIG="/path/to/config.yaml"

# Data directory
export VOICE_BRIDGE_DATA_DIR="/path/to/data"

# GitHub token (for bug tracking)
export GITHUB_TOKEN="your_token_here"
```

Or put in `~/.config/voice-bridge/.env`:

```bash
echo "VOICE_BRIDGE_BACKEND_URL=ws://localhost:8765" >> ~/.config/voice-bridge/.env
```

---

## Verification

After installation, verify everything works:

```bash
# Check Python version
python3 --version

# Check package installed
pip list | grep voice-openclaw

# Check setup
ls ~/.config/voice-bridge/config.yaml
ls ~/.local/share/voice-bridge/

# Check service status
sudo systemctl status voice-bridge.service

# Check logs for errors
journalctl -u voice-bridge.service -n 20
```

---

## Upgrading

To upgrade to a new version:

```bash
# Stop service
sudo systemctl stop voice-bridge.service

# Pull latest changes
git fetch origin
git checkout <new_version>

# Update dependencies
pip install -e .

# Restart service
sudo systemctl start voice-bridge.service
```

---

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop voice-bridge.service
sudo systemctl disable voice-bridge.service

# Uninstall service
sudo ./scripts/uninstall.sh

# Uninstall Python package
pip uninstall voice-openclaw-bridge

# Remove configuration and data (optional)
rm -rf ~/.config/voice-bridge
rm -rf ~/.local/share/voice-bridge
```

---

## Troubleshooting

### Installation Issues

**Package installation fails:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Audio devices not detected:**
```bash
# Check audio devices
python3 -m bridge.main setup

# Install PortAudio
sudo apt-get install portaudio19-dev
```

### Service Issues

**Service won't start:**
```bash
# Check status
sudo systemctl status voice-bridge.service

# View logs
journalctl -u voice-bridge.service -n 50

# Check permissions
ls -l ~/.config/voice-bridge/
ls -l ~/.local/share/voice-bridge/
```

**No audio output:**
```bash
# Check audio devices in config
cat ~/.config/voice-bridge/config.yaml

# Test audio device
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Rerun setup wizard
python3 -m bridge.main setup
```

**OpenClaw connection fails:**
```bash
# Check OpenClaw is running
openclaw status

# Check backend URL in config
grep backend_url ~/.config/voice-bridge/config.yaml

# Test connection
wscat -c ws://localhost:8765  # Requires wscat
```

### Performance Issues

**STT transcription slow:**
- Use GPU: Set `stt.device = "cuda"`
- Use smaller model: Set `stt.model_size = "base"`

**High latency:**
- Check audio buffer settings
- Use wired network connection
- Reduce audio chunk size

---

## Support

- **Issues:** https://github.com/ray1caron/voice-openclaw-bridge-v2/issues
- **Documentation:** See project README and docs folder
- **Bug Tracking:** Use built-in bug tracking system (`python -m bridge.bug_cli`)

---

**Voice-OpenClaw Bridge v2 v1.0.0-beta - Production Installation Complete** ✅