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

## Sprint Status

**Sprint 2: Tool Integration - 100% Complete ✅**

| Issue | Component | Status | PR |
|-------|-----------|--------|-----|
| #17 | OpenClaw Middleware | ✅ Complete | #19 |
| #18 | Multi-Step Tool Handling | ✅ Complete | #19 |
| #8 | Bug Tracking System | ✅ Complete | - |

**Total:** 2/2 issues + bug tracker, 250+ tests passing

**Current:** Sprint 3 - Conversation Persistence (Issue #7)

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

# 2. Install dependencies
pip install -e "."

# 3. Run first-time setup (detects audio devices)
python scripts/setup.py

# 4. Start the bridge
python -m src.bridge.main
```

## Configuration

Configuration is stored in `~/.voice-bridge/config.yaml` and supports:

- **YAML config files** - Primary configuration
- **Environment variables** - Override with `BRIDGE__SECTION__KEY` format
- **.env file** - Load secrets from `~/.voice-bridge/.env`
- **Hot-reload** - Changes detected automatically (always on)

### First-Time Setup

Run `python scripts/setup.py` to:
- Detect audio input/output devices
- Generate configuration with recommended devices
- Create `.env` template for secrets

### Manual Configuration

Edit `~/.voice-bridge/config.yaml`:

```yaml
audio:
  input_device: "Blue Yeti Nano"  # or device index
  output_device: "USB Audio"
  sample_rate: 16000

stt:
  model: "base"  # tiny, base, small, medium, large
  language: null   # auto-detect if null

openclaw:
  host: "localhost"
  port: 8080

bridge:
  wake_word: "hey hal"
  hot_reload: true  # always on
```

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
| **Sprint 1** | ✅ Complete | 100% | #10 Config, #1 WebSocket, #2 Filtering, #3 Audio |
| **Sprint 2** | ✅ Complete | 100% | #17 Middleware, #18 Tool Chains, Bug Tracker |
| **Sprint 3** | 🔄 In Progress | 70% | #7 Conversation Persistence |
| Sprint 4 | ⏳ Planned | - | Interruption, Polish |

### Current: Sprint 3 - Conversation Persistence

**Completed:**
- ✅ Issue #7: Session Management (In Progress)
  - SQLite database schema with migrations
  - Session CRUD operations with UUID tracking
  - Conversation turn storage
  - Context window management with pruning
  - Session recovery after disconnects

**In Progress:**
- ⏳ Issue #7: Testing & Integration
  - 93 new tests created (debugging collection issues)
  - WebSocket client integration pending
  - Context persistence verification

**Files Added:**
- `src/bridge/conversation_store.py` (~400 lines)
- `src/bridge/session_manager.py` (~550 lines)
- `src/bridge/history_manager.py` (~600 lines)
- `src/bridge/context_window.py` (~450 lines)
- `src/bridge/session_recovery.py` (~500 lines)
- `tests/unit/test_session_manager.py` (~600 lines)
- `tests/unit/test_history_manager.py` (~700 lines)
- `tests/unit/test_context_window.py` (~600 lines)
- `tests/unit/test_session_recovery.py` (~650 lines)

**Previous Sprints:**
- See SPRINT2_PROGRESS.md for Sprint 2 details

## Contributing

See CONTRIBUTING.md for development guidelines. Check [existing issues](https://github.com/ray1caron/voice-openclaw-bridge-v2/issues) before creating new ones.

## License

MIT
