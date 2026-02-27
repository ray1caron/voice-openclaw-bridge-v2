# Voice-OpenClaw Bridge v2 — Implementation Plan v2.0

**Version:** 2.0  
**Date:** 2026-02-27 09:08 PST  
**Author:** Hal (OpenClaw Agent)  
**Status:** Active  

---

## Executive Summary

The Voice-OpenClaw Bridge v2 connects a local microphone/speaker setup to an OpenClaw session, enabling hands-free voice interaction with Hal. The user speaks → the bridge detects the wake word → captures speech → transcribes via Whisper → sends text to OpenClaw via the sessions HTTP API → streams the response → synthesizes speech via Piper TTS → plays back audio.

This is a local-first, privacy-preserving pipeline. No cloud STT/TTS required (though optional). The system runs as a Python daemon alongside the OpenClaw gateway.

**Key design decisions in v2.0:**
- Wake word: `"computer"` (built-in Porcupine keyword, no custom training required for MVP)
- OpenClaw integration: HTTP POST to `localhost:3000` sessions API (not a custom WebSocket endpoint)
- Threading: explicit asyncio + sounddevice callback bridge via `asyncio.Queue`
- Text-mode fallback (`--text-mode`) for CI and hardware-free testing
- Response filtering: heuristic-based for MVP; OpenClaw-native metadata as Phase 2

---

## Critical Pre-requisites — Day 0 Spike

**Before writing a single line of orchestrator code**, verify that the OpenClaw integration path works end-to-end.

### Day 0 Checklist

1. **Confirm OpenClaw gateway is running:**
   ```bash
   curl http://localhost:3000/health
   # Expected: {"status":"ok"} or similar
   ```

2. **List available sessions:**
   ```bash
   curl -s http://localhost:3000/api/sessions | jq .
   ```

3. **Send a test message to a session:**
   ```bash
   curl -s -X POST http://localhost:3000/api/sessions/main/send \
     -H "Content-Type: application/json" \
     -d '{"message": "hello from voice bridge spike test"}' | jq .
   ```

4. **Check response streaming behavior:**
   - Does the API return the full response synchronously, or does it stream chunks?
   - If streaming: capture the session output polling endpoint
   - If synchronous: single response works fine

5. **Fallback if WebSocket not available:**
   - Poll `GET /api/sessions/{id}/output?since={timestamp}` every 500ms
   - Or read response from POST body directly if synchronous
   - Document the actual API behavior in `docs/openclaw-api-notes.md`

6. **Spike output:** A working `spike_openclaw.py` script that sends a message and gets a response. This becomes the foundation of `openclaw_client.py`.

**Do not proceed to Day 1 until the spike passes.**

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice Bridge Daemon                       │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Audio    │    │ Wake     │    │ VAD /    │             │
│  │ Pipeline │───▶│ Word     │───▶│ Speech   │             │
│  │(capture) │    │ Detector │    │ Capture  │             │
│  └──────────┘    └──────────┘    └──────────┘             │
│       │                                │                    │
│       │ sounddevice                    │ raw PCM            │
│       │ C callback                     ▼                    │
│       │                         ┌──────────┐               │
│       │                         │ Whisper  │               │
│       │                         │ STT      │               │
│       │                         └──────────┘               │
│       │                                │ text              │
│       │                                ▼                    │
│       │                         ┌──────────┐               │
│       │                         │OpenClaw  │               │
│       │                         │HTTP      │               │
│       │                         │Client    │               │
│       │                         └──────────┘               │
│       │                                │ response text      │
│       │                                ▼                    │
│       │                         ┌──────────┐               │
│       │                         │ Response │               │
│       │                         │ Filter   │               │
│       │                         └──────────┘               │
│       │                                │ clean text         │
│       │                                ▼                    │
│       │                         ┌──────────┐               │
│       │                         │ Piper    │               │
│       │                         │ TTS      │               │
│       │                         └──────────┘               │
│       │                                │ audio              │
│       │                                ▼                    │
│       │◀───────────────────────┌──────────┐               │
│                                │ Playback │               │
│                                └──────────┘               │
└─────────────────────────────────────────────────────────────┘
         │ HTTP POST localhost:3000
         ▼
┌─────────────────────┐
│   OpenClaw Gateway  │
│   (Hal session)     │
└─────────────────────┘
```

### Threading Model (Critical)

`sounddevice` uses C-level audio callbacks that run in a **separate OS thread** — not the asyncio event loop. Bridging these two worlds requires explicit thread-safety.

```
┌─────────────────────────────────────────────────────────────┐
│  MAIN THREAD — asyncio event loop                           │
│                                                             │
│  async def audio_consumer():                                │
│      while True:                                            │
│          chunk = await audio_queue.get()  # async wait     │
│          await process_chunk(chunk)                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          ▲  asyncio.Queue (thread-safe bridge)
          │  loop.call_soon_threadsafe(audio_queue.put_nowait, chunk)
┌─────────────────────────────────────────────────────────────┐
│  AUDIO THREAD — sounddevice C callback                      │
│                                                             │
│  def audio_callback(indata, frames, time, status):          │
│      chunk = indata.copy()                                  │
│      loop.call_soon_threadsafe(                             │
│          audio_queue.put_nowait, chunk                      │
│      )                                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Rules:**
- **Never** call `asyncio` functions directly from the audio callback
- **Never** block in the audio callback (no I/O, no sleeps)
- Use `loop.call_soon_threadsafe()` as the **only** bridge from audio thread → asyncio
- `asyncio.Queue` is the buffer; size-limit it (e.g., `maxsize=100`) to prevent unbounded growth

**Full pattern:**

```python
import asyncio
import sounddevice as sd
import numpy as np

audio_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
loop: asyncio.AbstractEventLoop = None

def audio_callback(indata: np.ndarray, frames: int, time, status):
    """Called in C audio thread. Must be non-blocking."""
    if status:
        print(f"Audio status: {status}", flush=True)
    chunk = indata.copy()
    # Bridge to asyncio safely
    loop.call_soon_threadsafe(audio_queue.put_nowait, chunk)

async def audio_consumer():
    """Runs in asyncio event loop."""
    while True:
        chunk = await audio_queue.get()
        await process_chunk(chunk)

async def main():
    global loop
    loop = asyncio.get_running_loop()
    
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000):
        await audio_consumer()

asyncio.run(main())
```

---

## Module Descriptions

```
voice_bridge/
├── main.py                  # Entry point, CLI args, orchestrator
├── audio_pipeline.py        # sounddevice capture + asyncio.Queue bridge
├── wake_word.py             # Porcupine wake word detection ("computer")
├── vad.py                   # WebRTC VAD for speech endpoint detection
├── stt.py                   # Whisper STT (faster-whisper)
├── openclaw_client.py       # HTTP client for OpenClaw sessions API
├── response_filter.py       # Heuristic filter for clean TTS text
├── tts.py                   # Piper TTS → audio output
├── playback.py              # sounddevice playback
├── state_machine.py         # IDLE → LISTENING → TRANSCRIBING → SPEAKING
├── config.py                # Config dataclass, loaded from config.yaml
└── utils/
    ├── logging.py           # Structured logging
    └── audio_utils.py       # PCM conversion helpers
```

### Key Modules

**`audio_pipeline.py`**
- Opens sounddevice InputStream
- Audio callback puts chunks into `asyncio.Queue` via `loop.call_soon_threadsafe()`
- Async generator yields chunks to consumers

**`wake_word.py`**
- Wraps `pvporcupine` with keyword `"computer"` (built-in, no license file needed for MVP)
- Processes 512-sample frames (Porcupine requirement)
- Emits wake event to state machine
- **Phase 2:** Custom "Hey Hal" keyword via Picovoice Console model training

**`vad.py`**
- WebRTC VAD for speech endpoint detection (when to stop recording)
- 30ms frames at 16kHz
- Trailing silence detection: 600ms of silence → end of utterance

**`stt.py`**
- `faster-whisper` with `base.en` model for MVP
- Upgrade path: `small.en` or `medium.en` for accuracy
- Returns transcript string

**`openclaw_client.py`**
- HTTP POST to `http://localhost:3000/api/sessions/{session_id}/send`
- Session ID configurable (default: `main`)
- Handles response: synchronous or polling
- Based on Day 0 spike findings

**`response_filter.py`**  
See "Response Filtering" section below.

**`tts.py`**
- Calls `piper` subprocess with selected voice model
- Returns raw PCM audio bytes
- Voice configurable (default: `en_US-lessac-medium`)

---

## Response Filtering

### The Honest Assessment

**Ideal solution:** OpenClaw adds a metadata flag to responses indicating whether they're for voice output vs. internal processing. This would let the bridge make precise decisions. **This is out of scope for this project** — it requires changes to the OpenClaw gateway.

### MVP: Heuristic Filter

The bridge uses a heuristic filter that is "good enough" for practical use:

```python
import re

def filter_for_tts(text: str) -> str:
    """Heuristic filter to clean response text for TTS."""
    # Remove markdown formatting
    text = re.sub(r'```[\s\S]*?```', '[code block]', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s+', '', text)
    
    # Remove URLs (they're unreadable when spoken)
    text = re.sub(r'https?://\S+', '[link]', text)
    
    # Remove tool call artifacts (heuristic: lines starting with known patterns)
    lines = text.splitlines()
    filtered = [l for l in lines if not l.strip().startswith(('→', '↳', 'Tool:', 'exec:', 'read:'))]
    text = '\n'.join(filtered)
    
    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```

**"Good enough" means:**
- Conversational responses read naturally
- Code blocks are skipped (not read verbatim)
- Markdown formatting is stripped
- Tool call output lines are suppressed

**Known failure modes:**
- Can't reliably detect "internal" agent thoughts vs. user-facing responses
- Long responses with mixed content may sound awkward
- Heuristics may need tuning per use case

### Upgrade Path (Phase 2)

When OpenClaw adds response metadata:
1. Gateway includes `{"voice": true/false}` in response JSON
2. `openclaw_client.py` passes flag to filter
3. Filter becomes: if `voice=false`, skip entirely; if `voice=true`, pass through with minimal cleanup
4. No heuristics needed

---

## Implementation Phases

### Week 1 — Core Pipeline (Day by Day)

#### Day 0 (Pre-work): OpenClaw Integration Spike
- [ ] Verify OpenClaw gateway is accessible at `localhost:3000`
- [ ] Test session list endpoint
- [ ] Send test message via HTTP, capture response
- [ ] Document actual API shape in `docs/openclaw-api-notes.md`
- [ ] Write `spike_openclaw.py` — working proof of concept
- [ ] **Gate:** Do not proceed until this works

#### Day 1: Audio Capture + STT (Smoke Test)
- [ ] Set up project structure and `pyproject.toml`
- [ ] Implement `audio_pipeline.py` with asyncio.Queue bridge
- [ ] Implement basic `vad.py` with WebRTC VAD
- [ ] Implement `stt.py` with faster-whisper
- [ ] Wire together: mic → VAD → Whisper
- [ ] **Smoke test milestone:** Terminal shows `[TRANSCRIPT]: <your words>` when you speak
  - No OpenClaw connection required
  - No wake word required
  - Just raw "record speech → transcribe → print"

#### Day 2: Wake Word
- [ ] Install and configure `pvporcupine`
- [ ] Implement `wake_word.py` with keyword `"computer"`
- [ ] Test: say "computer" → log event fires
- [ ] Integrate with audio pipeline: gate STT on wake word detection
- [ ] Test full flow: "computer [pause] what time is it" → transcript

#### Day 3: OpenClaw Client
- [ ] Implement `openclaw_client.py` based on Day 0 spike
- [ ] Wire transcript → OpenClaw → response text
- [ ] Test: speak → transcribe → send to OpenClaw → print response
- [ ] Handle errors: gateway down, timeout, empty response

#### Day 4: TTS + Playback
- [ ] Install Piper and download voice model
- [ ] Implement `tts.py` and `playback.py`
- [ ] Wire response text → TTS → audio playback
- [ ] Implement `response_filter.py` heuristics
- [ ] Test full loop: speak → transcribe → OpenClaw → filtered response → speak back

#### Day 5: State Machine + Polish
- [ ] Implement `state_machine.py` (IDLE → LISTENING → TRANSCRIBING → SPEAKING → IDLE)
- [ ] Add barge-in detection (interrupt playback on new wake word)
- [ ] Add `--text-mode` CLI flag (see below)
- [ ] Basic error recovery and logging
- [ ] Manual end-to-end test: full voice conversation

### Week 2 — Hardening & Testing

- Unit tests for each module
- Integration tests with `--text-mode`
- Config file (`config.yaml`) with all tunable parameters
- Systemd service file for auto-start
- Logging to file with rotation
- Performance profiling (latency measurement per stage)
- README and setup docs

### Week 3 — Buffer & Integration Surprises

**This week is explicitly buffered.** Expect hardware and integration issues:
- Audio device selection and latency tuning
- Porcupine wake word false positive/negative tuning
- Whisper accuracy tuning (model size vs. latency)
- Piper voice model selection
- OpenClaw response streaming behavior edge cases
- Any Phase 2 enhancements that fit

**Phase 2 candidates (if time allows):**
- "Hey Hal" custom wake word (requires Picovoice Console training)
- OpenClaw metadata-based response filtering
- Conversation history context
- Multi-session support

---

## Text-Only Fallback Mode (`--text-mode`)

For CI, automated testing, and development without hardware:

```bash
python -m voice_bridge --text-mode
```

**Behavior in text mode:**
- No microphone input — reads from stdin
- No speaker output — prints TTS text to stdout
- Wake word detection bypassed
- VAD bypassed
- STT bypassed — stdin line = transcript
- OpenClaw integration remains active
- Response filter remains active

**Example session:**
```
$ python -m voice_bridge --text-mode
[TEXT MODE] Enter message (or Ctrl+C to quit):
> what's the weather like?
[OPENCLAW] Sending: "what's the weather like?"
[RESPONSE] It looks sunny and 68°F in your area today...
[TTS SKIPPED - text mode]
```

**Use in CI:**
```bash
echo "ping" | python -m voice_bridge --text-mode --session test
```

---

## Testing Plan

### Unit Tests
- `test_audio_pipeline.py` — mock sounddevice, verify queue behavior
- `test_vad.py` — synthetic PCM, verify speech/silence detection
- `test_stt.py` — pre-recorded WAV files → expected transcripts
- `test_response_filter.py` — markdown/URL/tool-call stripping
- `test_openclaw_client.py` — mock HTTP server, verify request shape
- `test_state_machine.py` — state transition coverage

### Integration Tests (all use `--text-mode`)
- Full pipeline: stdin text → OpenClaw → filtered response → stdout
- Error handling: gateway down, empty response, malformed JSON
- Barge-in simulation

### Hardware Tests (manual)
- Wake word sensitivity (false positive rate over 5 minutes of background noise)
- STT accuracy on 20 sample phrases
- End-to-end latency: wake word → audio response starts (target: <2s)
- Playback quality on target speaker hardware

---

## System Requirements

### Hardware (Development)
- Raspberry Pi 4 (4GB) or Linux x86_64 machine
- USB microphone (e.g., Blue Snowball or Jabra Speak 410)
- Speaker (3.5mm or USB)
- Minimum 2GB RAM free

### Software
- Python 3.11+
- OpenClaw gateway running at `localhost:3000`
- Dependencies:
  ```
  faster-whisper>=0.10.0
  pvporcupine>=3.0.0
  webrtcvad>=2.0.10
  sounddevice>=0.4.6
  soundfile>=0.12.1
  numpy>=1.26.0
  httpx>=0.27.0       # async HTTP client
  pyyaml>=6.0
  ```
- Piper TTS binary + voice model (downloaded separately)
- `faster-whisper` model: `base.en` (~145MB)

---

## Known Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenClaw HTTP API shape differs from assumed | High | High | Day 0 spike — don't skip it |
| Porcupine "computer" wake word too many false positives | Medium | Medium | Tune sensitivity; add confirmation beep |
| Whisper latency too high on Pi 4 | Medium | High | Use `base.en`; fallback to `tiny.en` |
| sounddevice/asyncio thread bridge race conditions | Medium | High | Explicit Queue maxsize; drain on shutdown |
| Piper TTS subprocess latency | Low | Medium | Pre-warm subprocess; stream audio chunks |
| OpenClaw response too long for TTS | Medium | Low | Truncate at N chars; filter to first paragraph |
| Hardware audio device issues (ALSA/PulseAudio) | High | Medium | Test early; document device IDs in config |
| Week 3 integration surprises (unknown unknowns) | High | Variable | Week 3 is explicitly buffered for this |

---

## Changelog: v1.0 → v2.0

| # | Change | Reason |
|---|--------|--------|
| 1 | Wake word changed from "Hey Hal" to "computer" | "Hey Hal" requires custom Picovoice model training (days of work + $$). "computer" is a built-in Porcupine keyword, works out of the box. "Hey Hal" documented as Phase 2. |
| 2 | Added Day 0 integration spike | v1.0 assumed OpenClaw had a custom `/voice` WebSocket endpoint. It doesn't. Must verify the actual API before building on top of it. |
| 3 | Explicit threading model documentation | v1.0 mentioned asyncio but didn't address the sounddevice C callback threading problem. This is a real footgun — made explicit with code pattern. |
| 4 | Added Day 1 smoke test milestone | v1.0 had no early validation gate. "Show mic audio being transcribed" is a concrete, achievable Day 1 target that doesn't require any OpenClaw integration. |
| 5 | Added `--text-mode` CLI flag | CI and development without hardware was not addressed. Text mode makes the pipeline testable anywhere. |
| 6 | Honest response filtering section | v1.0 implied metadata filtering was achievable. It requires OpenClaw changes. v2.0 documents heuristic approach, failure modes, and upgrade path. |
| 7 | OpenClaw integration via HTTP sessions API | v1.0 assumed a custom WebSocket voice endpoint. v2.0 uses the existing `sessions_send` HTTP equivalent at `localhost:3000`. |
| 8 | Week 3 explicitly buffered | v1.0 was optimistic about timeline. Hardware and integration surprises are inevitable. Week 3 is now a buffer week with Phase 2 stretch goals. |

---

*End of Implementation Plan v2.0*
