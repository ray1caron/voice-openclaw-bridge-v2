# Voice-OpenClaw Bridge v2

Bidirectional voice interface for OpenClaw. Speak your requests, hear the responses — no typing required.

## Architecture

```
Voice Input → STT → OpenClaw Agent → Response Filter → TTS → Voice Output
                ↑                           ↓
           Wake Word                   Internal thinking
           Detection                   (not spoken)
```

**Key Innovation:** Only final responses are spoken. Tool calls, thinking, and planning happen silently.

## Requirements

- Python 3.10+
- OpenClaw running locally
- USB Microphone
- Speakers
- CUDA-capable GPU (optional, for Whisper STT)

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/ray1caron/voice-openclaw-bridge-v2.git
cd voice-openclaw-bridge-v2

# 2. Run setup
./scripts/setup.sh

# 3. Configure
# Edit ~/.config/voice-bridge-v2/config.yaml

# 4. Run
python -m src.bridge.main
```

## Configuration

See `config/default.yaml` for all options.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint
ruff check src/

# Type check
mypy src/
```

## Project Structure

```
src/
├── bridge/      # WebSocket client and orchestration
├── audio/       # Audio I/O (capture/playback)
├── stt/         # Speech-to-text (Whisper)
├── tts/         # Text-to-speech (Piper)
└── wake/        # Wake word detection

tests/           # Test suite
docs/            # Documentation
scripts/         # Utility scripts
systemd/         # Systemd service files
```

## Sprint Progress

Track development on the [GitHub Project Board](https://github.com/ray1caron/voice-openclaw-bridge-v2/projects).

| Sprint | Status | Progress | Key Deliverables |
|--------|--------|----------|------------------|
| **Sprint 1** | 🔄 In Progress | 25% | #10 Config ✅, #1 WebSocket, #2 Filtering, #3 Audio |
| Sprint 2 | ⏳ Planned | - | Tool Integration |
| Sprint 3 | ⏳ Planned | - | Memory & Context |
| Sprint 4 | ⏳ Planned | - | Polish & Docs |

### Current: Sprint 1 - Foundation

**Completed:**
- ✅ Issue #10: Configuration System (PR #11 ready)
  - YAML config with hot-reload
  - Audio device discovery
  - Environment variables + .env support
  - 28/28 tests passing

**In Progress:**
- ⏳ Issue #1: WebSocket Client
- ⏳ Issue #2: Response Filtering  
- ⏳ Issue #3: Audio Pipeline

## Contributing

See CONTRIBUTING.md for development guidelines. Check [existing issues](https://github.com/ray1caron/voice-openclaw-bridge-v2/issues) before creating new ones.

## License

MIT
