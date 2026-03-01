# Voice-OpenClaw Bridge v2 - User Guide

**Version:** 1.0.0-beta
**Last Updated:** 2026-02-28
**Status:** Production Ready ✅

---

## Quick Start

### Production Usage (Systemd)

```bash
# Start service
sudo systemctl start voice-bridge.service

# Check status
sudo systemctl status voice-bridge.service

# View logs
journalctl -u voice-bridge.service -f
```

### Development Usage

```bash
# Run directly
python3 -m bridge.main

# Run with specific config
python3 -m bridge.main --config /path/to/config.yaml
```

---

## Table of Contents

1. [How It Works](#how-it-works)
2. [First Use](#first-use)
3. [Voice Interaction](#voice-interaction)
4. [Common Tasks](#common-tasks)
5. [Configuration](#configuration)
6. [Monitoring & Logs](#monitoring--logs)
7. [Bug Tracking](#bug-tracking)
8. [Troubleshooting](#troubleshooting)

---

## How It Works

Voice-OpenClaw Bridge enables voice interactions with OpenClaw through:

```
You Speak → Wake Word → Audio Capture → STT → OpenClaw → TTS → Audio Output
```

### Flow

1. **Wake Word** - Say "computer" to activate
2. **Audio Capture** - Records your speech until silence
3. **STT (Speech-to-Text)** - Transcribes audio to text
4. **OpenClaw** - Sends text to OpenClaw via WebSocket
5. **Response Filter** - Filters out thinking/tool calls
6. **TTS (Text-to-Speech)** - Converts response to audio
7. **Audio Playback** - Plays the response
8. **Barge-In** - Can interrupt during playback

---

## First Use

### Step 1: Wake Up the Assistant

Say **"computer"** clearly.

**Response:** Assistant says "listening..." and starts recording.

### Step 2: Ask a Question

Wait 1-2 seconds for "listening...", then speak:

```
"computer, what's the weather today?"
```

### Step 3: Listen to Response

Assistant processes and responds with audio.

**Response:** "The weather today is..."

### Step 4: Ask Follow-up Questions

Continue conversation without repeating wake word:

```
"what about tomorrow?"
```

**Note:** After waking up, the assistant stays active for timeout period (default 30 seconds).

---

## Voice Interaction

### Wake Word

**Keyword:** "computer"

**Tips:**
- Speak clearly and at normal volume
- Wait 1-2 seconds after waking before speaking
- Wake word can be reconfigured in settings

### Asking Questions

**After wake word:**
- Speak naturally at normal speed
- Complete your thought (wait for silence detection)
- Assistant will transcribe the whole sentence

**Example prompts:**
- Information: "What's the capital of France?"
- Calculation: "What's 123 times 45?"
- Creative: "Write a haiku about cats"
- Assistance: "Remind me to call mom at 5pm"

### Barge-In (Interruption)

**Interrupt while assistant is speaking:**

Just start speaking during TTS playback.

**What happens:**
- Assistant stops speaking immediately
- Wake word detection reactivates
- Can ask new question

**Latency:** <100ms interruption time

### Conversation Context

The assistant maintains context from previous questions:

```
User: "Who is Albert Einstein?"
Assistant: "Albert Einstein was a German theoretical physicist..."

User: "When was he born?"
Assistant: "He was born on March 14, 1879..."
```

Context window preserves last several interactions.

---

## Common Tasks

### Get Current Time

```
"computer, what time is it?"
```

### Get Weather

```
"computer, what's the weather today?"
```

### Set Reminder

```
"computer, remind me to call mom at 5pm"
```

### Perform Calculation

```
"computer, what's 123 times 456?"
```

### Get Information

```
"computer, tell me about the history of Rome"
```

### Tell Joke

```
"computer, tell me a joke"
```

### Write Code

```
"computer, write a Python function to reverse a list"
```

### Translate

```
"computer, translate 'hello' to Spanish"
```

### Summarize Text

```
"computer, summarize this article..."
```

---

## Configuration

### Audio Settings

Modify `~/.config/voice-bridge/config.yaml`:

```yaml
audio:
  input_device: "default"  # Your microphone
  output_device: "default"  # Your speakers
  sample_rate: 16000
  chunk_size: 1024
```

**Discover available devices:**
```bash
python3 -m bridge.main setup
```

### OpenClaw Connection

```yaml
openclaw:
  backend_url: "ws://localhost:8765"
  session_id: "voice-session"
  timeout: 30
```

### Response Filtering

**What gets spoken:**
- ✅ Final responses
- ✅ Questions from OpenClaw
- ✅ Short confirmations

**What stays silent:**
- ❌ Thinking messages
- ❌ Tool call messages
- ❌ Planning messages
- ❌ Progress indicators

You can adjust filtering in config.

---

## Monitoring & Logs

### Service Status

```bash
# Check if running
sudo systemctl status voice-bridge.service

# View recent logs
journalctl -u voice-bridge.service -n 50

# Follow logs live
journalctl -u voice-bridge.service -f
```

### Log Messages

**Normal operation:**
```
[INFO] Wake word detected
[INFO] Audio captured (2.3s)
[INFO] Transcription: what's the weather
[INFO] Speaking response...
```

**Warnings:**
```
[WARNING] Audio buffer nearly full
[WARNING] High transcription latency
```

**Errors:**
```
[ERROR] Microphone not found
[ERROR] OpenClaw connection failed
[ERROR] STT transcription failed
```

### Statistics

The assistant tracks statistics including:
- Number of interactions
- Total speaking time
- Number of interruptions/barge-ins
- Average transcription latency
- Average TTS latency

---

## Bug Tracking

v1.0.0-beta includes automated bug tracking.

### Viewing Bugs

```bash
# List all bugs
python -m bridge.bug_cli list

# Show specific bug
python -m bridge.bug_cli show <bug_id>

# Get statistics
python -m bridge.bug_cli stats
```

### Exporting Bugs

```bash
# Export to JSON
python -m bridge.bug_cli export bugs.json

# Export to Markdown
python -m bridge.bug_cli export bugs.md --format markdown

# Export to CSV
python -m bridge.bug_cli export bugs.csv --format csv
```

### Automatic Bug Capture

Errors are automatically captured with full context:
- Python version and platform
- Audio devices
- Configuration state
- Stack trace

**See:** [BUG_TRACKER.md](BUG_TRACKER.md) for complete guide

---

## Advanced Usage

### Voice Commands

The assistant can understand special commands:

```
"computer, set volume to 50%"
"computer, pause music"
"computer, what can you do?"
```

**Note:** Command support depends on OpenClaw configuration.

### Custom Wake Word

Use Porcupine console to create custom wake word:
1. Sign up at https://console.picovoice.ai/
2. Train custom wake word
3. Get access key
4. Update config with access key

---

## Troubleshooting

### Wake Word Not Detected

**Cause:** Microphone not working or configured incorrectly.

**Solutions:**
```bash
# Check microphone
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Rerun audio setup
python3 -m bridge.main setup

# Check system audio
pactl list sources  # PulseAudio
arecord -l  # ALSA
```

### No Audio Output

**Cause:** Speaker not configured.

**Solutions:**
```bash
# Check speakers
aplay -L

# Rerun audio setup
python3 -m bridge.main setup

# Test system audio
speaker-test -t wav -c 2
```

### OpenClaw Connection Failed

**Cause:** OpenClaw not running or wrong URL.

**Solutions:**
```bash
# Check OpenClaw status
openclaw status

# Test connection
wscat -c ws://localhost:8765

# Check config
grep backend_url ~/.config/voice-bridge/config.yaml
```

### Slow Transcription

**Cause:** STT model too large or CPU-only.

**Solutions:**
```yaml
# Use smaller model
stt:
  model_size: "base"  # or "tiny"

# Use GPU if available
stt:
  device: "cuda"
```

### Barge-In Not Working

**Cause:** Audio buffer settings or VAD sensitivity.

**Solutions:**
```yaml
# Adjust VAD
audio:
  vad_aggressiveness: 3  # 0-3, higher = more sensitive

# Adjust buffer
audio:
  buffer_size: 2048  # Lower = faster interruption
```

---

## Best Practices

### Speaking

- **Speak clearly** at normal volume
- **Wait 1-2 seconds** after wake word before speaking
- **Complete your thought** (let silence detection finish)
- **Ask one question at a time** for best accuracy

### Environment

- **Quiet environment** works best
- **Avoid background noise** if possible
- **Position microphone** close to mouth (1-2 feet)
- **Test audio levels** in setup wizard

### Performance

- **Use wired network** if remote OpenClaw
- **Use GPU** for STT to reduce latency
- **Use smaller model** if CPU-only

---

## Tips & Tricks

### Faster Responses

- Use smaller STT model (`base` or `tiny`)
- Use GPU for STT
- Reduce audio chunk size

### Better Accuracy

- Speak clearly and slowly
- Use a good quality microphone
- Reduce background noise

### Lower CPU Usage

- Use larger STT model (fewer compute cycles)
- Increase audio chunk size
- Reduce concurrent sessions

---

## Getting Help

### Documentation

- [README.md](README.md) - Overview
- [INSTALL.md](INSTALL.md) - Installation
- [BUG_TRACKER.md](BUG_TRACKER.md) - Bug tracking guide

### Community

- **Issues:** https://github.com/ray1caron/voice-openclaw-bridge-v2/issues
- ** Discussions:** Coming soon

### Support

- Check logs: `journalctl -u voice-bridge.service -n 100`
- Run bug tracker: `python -m bridge.bug_cli list`
- Report issues with full context

---

## FAQ

**Q: Can I change the wake word?**

A: Yes! Use Porcupine console to create custom wake word.

**Q: Does this work offline?**

A: STT and TTS run locally, but OpenClaw requires connection to backend (can be localhost).

**Q: Can I use a different language?**

A: Yes! Configure language in settings. See INSTALL.md for details.

**Q: How much RAM does it use?**

A: ~1-2 GB with medium-sized models. Larger models use more.

**Q: Can I run multiple instances?**

A: Yes! Each instance needs its own config and session ID.

---

**Voice-OpenClaw Bridge v2 v1.0.0-beta - Production Ready** ✅