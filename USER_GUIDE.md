# Hal Voice Assistant - User Guide

Complete instructions for using your local AI voice assistant.

**Repository:** https://github.com/ray1caron/local-voice  
**Location:** `~/openclaw-workspace/voice-assistant/`  
**Hardware:** RTX 5070 (GPU-accelerated)

---

## Quick Start

Open a terminal and run:

```bash
cd ~/openclaw-workspace/voice-assistant
./run_hal.sh
```

That's it! The assistant will start and tell you what to do.

---

## How It Works

Your voice assistant follows this flow:

```
You Speak → Wake Word → Question → Processing → Hal Speaks
```

1. **Wake Word Detection** (Porcupine) - Listens for "computer"
2. **Speech Recognition** (Whisper) - Converts speech to text
3. **Thinking** (Ollama) - Processes your question
4. **Speaking** (Piper) - Converts answer to speech

---

## Basic Usage

### Starting the Assistant

There are multiple ways to start:

**Method 1: Launcher Script (Recommended)**
```bash
./run_hal.sh
```

**Method 2: Direct Python**
```bash
./venv/bin/python voice.py
```

**Method 3: With Virtual Environment**
```bash
source venv/bin/activate
python voice.py
```

---

## Speaking to Hal

### Step 1: Wake Word

Say **"computer"** clearly to activate Hal.

**What happens:**
- Hal is listening constantly
- When you say "computer", wake word detector triggers
- Hal responds with "listening..."

### Step 2: Ask Your Question

Wait 1-2 seconds for "listening...", then ask anything:

- "What time is it?"
- "Tell me a joke"
- "What is the capital of Japan?"
- "Explain quantum computing"
- "What's 15 times 37?"

### Step 3: Listen to Response

Hal will:
1. Convert speech to text (Whisper)
2. Think about answer (Ollama qwen2.5:14b)
3. Speak response (Piper TTS)

**Typical response time:** 1-3 seconds

### Step 4: Continue or Stop

- **Say "computer" again** for another question
- **Press Ctrl+C** to stop the assistant

---

## Commands Reference

### Launcher Commands

| Command | Description |
|---------|-------------|
| `./run_hal.sh` | Run full voice assistant (default) |
| `./run_hal.sh wakeword` | Test wake word detection only |
| `./run_hal.sh status` | Check system status |
| `./run_hal.sh setup` | Run setup diagnostics |
| `./run_hal.sh help` | Show all commands |

### Wake Word Test

Test just the wake word (faster, lighter):

```bash
./run_hal.sh wakeword
```

**What to do:**
1. Wait for "Listening for wake word..."
2. Say "computer"
3. Test exits when detected

Useful for checking microphone is working.

---

## Example Conversations

### Example 1: Simple Question
**You:** "Computer"
**Hal:** [listening indicator]
**You:** "What time is it?"
**Hal:** "It's 2:15 PM."

### Example 2: Follow-up
**You:** "Computer"
**You:** "What day is it?"
**Hal:** "It's Friday, February 20th."
**You:** "Computer"
**You:** "Thanks, Hal"
**Hal:** "You're welcome!"

### Example 3: Knowledge Question
**You:** "Computer"
**You:** "What is the speed of light?"
**Hal:** "The speed of light is approximately 299,792 kilometers per second."

---

## Tips for Best Results

### Microphone
- **Speak clearly** - Don't mumble
- **Moderate volume** - Not too loud, not too quiet
- **Reduce background noise** - Turn off TV/music if possible
- **3-6 inches from mic** - Optimal distance

### Wake Word
- **"Computer"** is the wake word (can be changed in code)
- **Built-in alternatives:** jarvis, alexa, hey google
- **Custom wake words:** Require Porcupine account

### Questions
- **Keep it natural** - Ask as you would to a person
- **One question at a time** - Wait for response
- **Short questions** - Long speeches may get cut off

### Interrupting
- **Barge-in supported** - Say "computer" while Hal is talking to interrupt
- **Stop speaking** - Hal will detect silence and stop

---

## Troubleshooting

### "No microphone detected"

**Cause:** Microphone not connected or not recognized

**Fix:**
```bash
# Check connected microphones
arecord -l

# If none listed:
# 1. Check USB connection
# 2. Try different USB port
# 3. Check Ubuntu Settings → Sound → Input
```

### "Wake word not working"

**Cause:** Audio too quiet, background noise, or wrong device

**Fix:**
1. **Test microphone:** `arecord -d 5 test.wav && aplay test.wav`
2. **Check levels:** Ubuntu Settings → Sound → Input
3. **Run wake word test only:** `./run_hal.sh wakeword`
4. **Speak louder and clearer**

### "Slow response time"

**Cause:** First run, GPU not being used, or model loading

**Fix:**
```bash
# Check GPU is being used
nvidia-smi

# Should show python using GPU memory
# If not, check workers.py has:
# WHISPER_DEVICE = "cuda"
# WHISPER_COMPUTE_TYPE = "float16"
```

### "Out of memory error"

**Cause:** VRAM exhausted (RTX 5070 has 16GB)

**Fix:**
```bash
# Check VRAM usage
watch -n 1 nvidia-smi

# If full, use smaller model in workers.py:
# WHISPER_MODEL = "small"  # Instead of "medium"
# Uses 2GB instead of 5GB
```

### "Hal speaks too fast/slow"

**Cause:** Token streaming or TTS settings

**Fix:**
- Normal - streaming is designed for low latency
- If choppy: Check speakers, reduce system load

### "No audio output"

**Cause:** Wrong audio device selected

**Fix:**
```bash
# List audio devices
./venv/bin/python -c "import sounddevice as sd; print(sd.query_devices())"

# Check Ubuntu Settings → Sound → Output
```

---

## Voice Commands Cheat Sheet

### Time & Date
- "What time is it?"
- "What day is today?"
- "What's today's date?"

### Math
- "What's 15 times 23?"
- "Calculate 156 divided by 4"
- "What's the square root of 144?"

### General Knowledge
- "Who invented the telephone?"
- "What is the capital of France?"
- "How far is the moon?"
- "Explain photosynthesis"

### Fun
- "Tell me a joke"
- "Give me a fun fact"
- "What's a good movie?"

### System
- "Computer" - activates listening
- Ctrl+C - stops assistant

---

## Configuration

### Changing Wake Word

Edit `wakeword.py`:

```python
# Free built-in options:
WAKE_WORD = "computer"  # default
WAKE_WORD = "jarvis"
WAKE_WORD = "alexa"
WAKE_WORD = "hey google"

# Multiple wake words:
WAKE_WORDS = ["computer", "jarvis"]
```

### Changing Voice Model

Download a different Piper voice:

```bash
cd voices
# Download desired voice from:
# https://github.com/rhasspy/piper/blob/master/VOICES.md

# Example: Ryan (male voice)
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json
```

Then update `workers.py`:
```python
PIPER_VOICE = "./voices/en_US-ryan-medium.onnx"
PIPER_VOICE_JSON = "./voices/en_US-ryan-medium.json"
```

### Changing AI Model

Edit `voice.py`:

```python
# Faster, smaller model:
LLM_MODEL = "qwen2.5:7b"  # 4GB VRAM

# Larger, smarter model:
LLM_MODEL = "qwen2.5:32b"  # 16GB VRAM (max out)

# Different model entirely:
LLM_MODEL = "llama3.2:3b"
```

### Changing Speech Recognition

Edit `workers.py`:

```python
# Accuracy vs Speed tradeoff:
WHISPER_MODEL = "tiny"    # 1GB, fastest, less accurate
WHISPER_MODEL = "base"    # 2GB, fast
WHISPER_MODEL = "small"   # 2GB, good balance
WHISPER_MODEL = "medium"  # 5GB, best balance (default)
WHISPER_MODEL = "large-v3" # 10GB, most accurate
```

---

## Advanced Usage

### Running Without Wake Word

To always listen (no wake word):

Edit `voice.py`:
```python
USE_WAKE_WORD = False
```

### Custom Personality

Edit the system prompt in `voice.py`:

```python
SYSTEM_PROMPT = """
You are Hal, a helpful AI assistant. Answer concisely and naturally, 
as if speaking in conversation. Keep responses to 1-2 sentences when possible.
"""
```

Change to:
```python
SYSTEM_PROMPT = """
You are a wise old wizard. Speak in riddles and mystical terms.
Keep it brief but cryptic.
"""
```

### API Mode

Use programmatically:

```python
from voice import LocalVoice

assistant = LocalVoice()
assistant.run()  # Starts interactive mode
```

---

## Files & Directories

```
voice-assistant/
├── run_hal.sh              # Launcher script ⭐ START HERE
├── voice.py                 # Main assistant
├── wakeword.py              # Wake word module
├── workers.py               # STT/TTS workers
├── test_wakeword.py         # Wake word test
├── venv/                    # Python environment
│   └── bin/python           # Python interpreter
├── models/                  # Whisper models
│   └── models--Systran--faster-whisper-medium/
├── voices/                  # Piper voices
│   ├── en_US-amy-medium.onnx
│   └── en_US-amy-medium.onnx.json
├── README.md                # Project readme
├── INSTALL.md               # Installation guide
└── USER_GUIDE.md            # This file
```

---

## VRAM Usage

Current configuration:
- Whisper medium: ~5GB
- Ollama qwen2.5:14b: ~8GB
- **Total: ~13GB / 16GB** ✅

Room for other apps: ~3GB

---

## Updates

### Updating Code
```bash
git pull origin master
```

### Updating Models
```bash
# Re-download whisper model
rm -rf models/
./run_hal.sh
# Auto-downloads on first run
```

### Updating Dependencies
```bash
./venv/bin/pip install --upgrade faster-whisper piper-tts ollama
```

---

## Getting Help

### Check Status
```bash
./run_hal.sh status
```

### Test Components
```bash
# Wake word only
./run_hal.sh wakeword

# Full assistant
./run_hal.sh

# Setup diagnostics
./run_hal.sh setup
```

### Logs

View recent output:
```bash
# Last run
./run_hal.sh 2>&1 | tee hal.log
```

---

## System Requirements

### Minimum
- RTX 5070 or equivalent (16GB VRAM)
- 16GB system RAM
- Microphone
- Speakers/headphones
- Ubuntu 24.04

### Recommended
- RTX 5070 (confirms GPU acceleration)
- USB microphone or headset
- Quiet environment
- Python 3.12+

---

## Privacy & Security

✅ **Fully Local** - Nothing leaves your machine  
✅ **No Cloud** - No internet required after setup  
✅ **Your Data** - Only you can access conversations  
✅ **Open Source** - Code inspectable and modifiable

---

## License

Based on Robin-07/local-voice, modified by ray1caron.

---

**Version:** 1.0  
**Last Updated:** 2026-02-20  
**Status:** Production Ready ✅

Enjoy your conversations with Hal! 🎙️
