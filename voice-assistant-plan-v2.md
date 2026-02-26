# Voice Assistant V2: Bidirectional OpenClaw Voice Interface

**For:** Ray (hal-System-Product-Name)  
**Date:** 2026-02-21  
**Goal:** Transform the local voice assistant into a bidirectional voice interface for OpenClaw

---

## Executive Summary

V2 evolves the standalone voice assistant into a **bidirectional voice bridge** for OpenClaw. Users speak naturally → OpenClaw processes with full tool access → responses spoken back. Critical innovation: intelligent filtering to ensure only **final, user-facing responses** reach TTS, not internal tool calls, thinking, or planning.

**Key Architectural Shifts:**
- ❌ Direct Ollama connection (bypasses OpenClaw tools)
- ✅ OpenClaw-native processing (full tool access, MEMORY.md context, skills)
- ✅ Response filtering pipeline (eliminates internal chatter)
- ✅ Session-aware conversation context

---

## Architecture Overview

### V2 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BIDIRECTIONAL VOICE INTERFACE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐     ┌──────────────────┐     ┌──────────────────────────────┐   │
│  │  Microphone │────→│  STT Engine      │────→│  OpenClaw Voice Bridge       │   │
│  │             │     │  (Whisper)       │     │  (WebSocket/HTTP Client)     │   │
│  └─────────────┘     └──────────────────┘     └──────────────┬───────────────┘   │
│                                                              │                   │
│                          ┌───────────────────────────────────┘                   │
│                          │                                                       │
│                          ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         OPENCLAW SESSION                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Tool Engine  │  │ Memory       │  │ Reasoning    │  │ Skills       │  │   │
│  │  │ (Web Search, │  │ (MEMORY.md,  │  │ (Chain of    │  │ (Custom      │  │   │
│  │  │  Files, etc) │  │  Context)    │  │  Thought)    │  │  Modules)    │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                           │                                              │   │
│  │                           ▼                                              │   │
│  │                   ┌──────────────┐                                       │   │
│  │                   │ LLM Core     │                                       │   │
│  │                   │ (Ollama)     │                                       │   │
│  │                   └──────┬───────┘                                       │   │
│  │                          │                                               │   │
│  │                          ▼                                               │   │
│  │                   ┌──────────────┐                                       │   │
│  │                   │ Response     │                                       │   │
│  │                   │ Filter       │◄── [METADATA: final=true/false]      │   │
│  │                   │ (Final only) │                                       │   │
│  │                   └──────┬───────┘                                       │   │
│  └──────────────────────────┼──────────────────────────────────────────────┘   │
│                             │                                                    │
│                             │ WebSocket/HTTP                                     │
│                             │ (tagged final response)                             │
│                             ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                          VOICE OUTPUT PIPELINE                           │   │
│  │  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │   │
│  │  │  TTS Engine  │────→│  Audio       │────→│  Speakers    │            │   │
│  │  │  (Piper)     │     │  Playback    │     │              │            │   │
│  │  └──────────────┘     └──────────────┘     └──────────────┘            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  USER    │───→│  AUDIO   │───→│   STT    │───→│ OPENCLAW │───→│   LLM    │
│  SPEAKS  │    │  CAPTURE │    │ (TEXT)   │    │  BRIDGE  │    │ PROCESS  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                                    │
                              ┌─────────────────────────────────────┘
                              │
                              ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  USER    │←───│  SPEAKER │←───│   TTS    │←───│ RESPONSE │←───│ FILTER   │
│  HEARS   │    │  AUDIO   │    │ (VOICE)  │    │  QUEUE   │    │ (FINAL)  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## OpenClaw Integration Protocol

### Protocol Comparison

| Aspect | WebSocket | HTTP Streaming | Recommendation |
|--------|-----------|----------------|----------------|
| **Latency** | Lowest (<50ms) | Medium (100-200ms) | WebSocket for voice |
| **Complexity** | Higher | Lower | HTTP for v2 MVP, WS for v2.5 |
| **Session State** | Built-in | Requires polling | WebSocket preferred |
| **OpenClaw Support** | Native (sessions) | Via REST API | Match OpenClaw capability |
| **Error Recovery** | Auto-reconnect | Retry logic needed | WebSocket auto-reconnect |

### Phase 1: HTTP Streaming (MVP)

Use OpenClaw's existing REST endpoints with Server-Sent Events (SSE):

```python
# voice_bridge/client.py
import requests
import json

class OpenClawVoiceClient:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.session_id = None
    
    def send_voice_input(self, text: str) -> str:
        """Send transcribed voice to OpenClaw, receive final response only"""
        url = f"{self.base_url}/api/voice/chat"
        
        payload = {
            "message": text,
            "session_id": self.session_id,
            "voice_mode": True,  # Signal: filter for final responses
            "channel": "voice"
        }
        
        response = requests.post(url, json=payload, stream=True)
        
        # Parse SSE stream for final response only
        final_response = ""
        for line in response.iter_lines():
            if line:
                event = json.loads(line.decode('utf-8'))
                if event.get("type") == "final":
                    final_response = event.get("content")
                    break
                # Skip: "thinking", "tool_call", "tool_result", "progress"
        
        return final_response
```

### Phase 2: WebSocket (Production)

WebSocket enables true bidirectional streaming and interruption handling:

```javascript
// voice_bridge/ws_client.js
class OpenClawVoiceSocket {
  constructor() {
    this.ws = new WebSocket('ws://localhost:3000/voice');
    this.audioQueue = [];
    this.setupHandlers();
  }
  
  setupHandlers() {
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      
      switch(msg.type) {
        case 'text_delta':
          // Accumulate text, don't TTS yet
          this.accumulateText(msg.content);
          break;
          
        case 'final':
          // Only now trigger TTS
          this.speak(msg.content);
          break;
          
        case 'interruption':
          // User started speaking, cancel current output
          this.cancelPlayback();
          break;
          
        case 'session_id':
          this.sessionId = msg.content;
          break;
      }
    };
  }
  
  sendTranscription(text) {
    this.ws.send(JSON.stringify({
      action: 'transcribe',
      text: text,
      session_id: this.sessionId
    }));
  }
}
```

### OpenClaw API Requirements

OpenClaw needs these endpoints for voice integration:

```yaml
# POST /api/voice/chat (HTTP)
Request:
  message: string           # Transcribed user speech
  session_id: string?      # For conversation continuity
  voice_mode: true         # Enable filtering
  
Response (SSE):
  - event: thinking        # Skip TTS
  - event: tool_call      # Skip TTS
  - event: tool_result     # Skip TTS
  - event: delta          # Skip TTS (intermediate)
  - event: final          # ✓ TTS THIS

# WebSocket /voice (Bidirectional)
Client → Server:
  - transcribe: {text, session_id}
  - interruption: {}      # User started speaking
  - continue: {}           # Acknowledge end of turn
  
Server → Client:
  - session_id: string
  - text_delta: string     # Accumulate but don't speak
  - final: string          # ✓ TTS THIS
  - interruption: {}       # Clear TTS queue
```

---

## Response Filtering Strategy

### The Problem

OpenClaw's typical response contains:
```
[tool_call: web_search("weather today")]
[tool_result: "72°F, sunny"]
<thinking>Drafting response about nice weather...</thinking>
It's a beautiful 72°F with sunny skies today!
```

**Goal:** Only TTS the last line.

### Filtering Approaches

| Approach | How It Works | Pros | Cons |
|----------|--------------|------|------|
| **A: Metadata Tags** | OpenClaw adds `{"final": true}` markers | Explicit, reliable | Requires OpenClaw changes |
| **B: Heuristic Parser** | Detect thinking blocks, tool calls | No OpenClaw changes needed | Fragile, may miss edge cases |
| **C: Streaming Filter** | Filter tokens in real-time | Low latency | Complex to implement |

**Recommendation:** Use A with B as fallback.

### Implementation: Metadata-Based Filtering

```python
# openclaw/plugins/voice_filter.py

class VoiceFilterPlugin:
    """
    OpenClaw plugin that marks final vs internal responses
    for voice interfaces.
    """
    
    def on_response_start(self, context):
        context.is_final = False
        context.buffer = []
    
    def on_thinking_start(self, context):
        context.is_thinking = True
        # Emit metadata but don't queue for TTS
        yield {"type": "thinking", "speakable": False}
    
    def on_thinking_end(self, context):
        context.is_thinking = False
    
    def on_tool_call(self, tool_name, params, context):
        # Tool calls are never spoken
        yield {
            "type": "tool_call",
            "tool": tool_name,
            "speakable": False
        }
    
    def on_tool_result(self, result, context):
        # Tool results might be displayed but not spoken directly
        yield {
            "type": "tool_result", 
            "speakable": False,
            "display": True
        }
    
    def on_response_chunk(self, text, context):
        context.buffer.append(text)
        # Intermediate chunks accumulate but aren't final
        yield {"type": "delta", "content": text, "speakable": False}
    
    def on_response_end(self, context):
        # Mark accumulated buffer as final
        final_text = "".join(context.buffer)
        yield {
            "type": "final",
            "content": final_text,
            "speakable": True  # ✓ This goes to TTS
        }
```

### Fallback: Heuristic Filter

If OpenClaw changes are delayed:

```python
# voice_bridge/fallback_filter.py
import re

class HeuristicVoiceFilter:
    """
    Client-side filter when OpenClaw doesn't provide metadata.
    Detects and removes internal content.
    """
    
    # Patterns to exclude from TTS
    SKIP_PATTERNS = [
        r'\[tool_call:.*?\]',           # Tool invocations
        r'\[tool_result:.*?\]',         # Tool results
        r'<thinking>.*?</thinking>',      # Thinking blocks
        r'<reasoning>.*?</reasoning>',    # Reasoning blocks
        r'<plan>.*?</plan>',              # Planning blocks
        r'Let me (search|check|look up|find|verify).*?\.',  # Self-directed actions
        r'I need to (search|check|look).*?\.',              # Planning language
        r'^(Searching|Checking|Looking up|Querying)\b',    # Action prefixes
    ]
    
    def filter(self, text: str) -> str | None:
        """Returns filtered text or None if should be skipped entirely"""
        
        # Check if it's purely internal
        for pattern in self.SKIP_PATTERNS:
            if re.match(pattern, text, re.DOTALL | re.IGNORECASE):
                return None
        
        # Remove embedded internal content
        filtered = text
        for pattern in self.SKIP_PATTERNS:
            filtered = re.sub(pattern, '', filtered, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up artifacts
        filtered = re.sub(r'\n+', ' ', filtered).strip()
        filtered = re.sub(r'\s+', ' ', filtered)
        
        return filtered if filtered else None
```

---

## Session Management

### Requirements

Voice conversations need **persistent sessions** to maintain:
- Conversation history (last N turns)
- OpenClaw context (loaded files, skills state)
- User preferences (voice model, speed)

### Session Architecture

```
┌─────────────────────────────────────────────────────┐
│                 SESSION MANAGER                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Session ID: "voice-uuid-123"                       │
│  Created: 2026-02-21T10:30:00Z                      │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  Conversation History (last 10 turns)       │   │
│  ├─────────────────────────────────────────────┤   │
│  │  User: "What's the weather in Paris?"       │   │
│  │  OpenClaw: "It's 22°C and sunny in Paris."    │   │
│  │  User: "What about tomorrow?"                │   │
│  │  OpenClaw: "Tomorrow will be 19°C with..."   │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  OpenClaw Context                           │   │
│  ├─────────────────────────────────────────────┤   │
│  │  - Loaded file: project-roadmap.md          │   │
│  │  - Current directory: /workspace/project      │   │
│  │  - Tools used recently: web_search, file      │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  Audio Preferences                          │   │
│  ├─────────────────────────────────────────────┤   │
│  │  - TTS Voice: "amy"                         │   │
│  │  - Speech Rate: 1.0x                        │   │
│  │  - Volume: 0.8                              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Implementation

```python
# voice_bridge/session_manager.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid

@dataclass
class VoiceSession:
    id: str = field(default_factory=lambda: f"voice-{uuid.uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    # Conversation history
    history: List[Dict] = field(default_factory=list)
    max_history: int = 10
    
    # OpenClaw context references
    openclaw_session_id: Optional[str] = None
    loaded_files: List[str] = field(default_factory=list)
    working_directory: Optional[str] = None
    
    # Audio settings
    voice_model: str = "amy"
    speech_rate: float = 1.0
    
    def add_turn(self, user_text: str, assistant_text: str):
        """Add conversation turn"""
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_text,
            "assistant": assistant_text
        })
        # Trim to max
        self.history = self.history[-self.max_history:]
        self.last_activity = datetime.utcnow()
    
    def to_openclaw_messages(self) -> List[Dict]:
        """Convert to OpenClaw message format"""
        messages = []
        for turn in self.history:
            messages.append({"role": "user", "content": turn["user"]})
            messages.append({"role": "assistant", "content": turn["assistant"]})
        return messages
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        expiry = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, VoiceSession] = {}
        self.openclaw_mapping: Dict[str, str] = {}  # voice_id → openclaw_id
    
    def create_session(self) -> VoiceSession:
        session = VoiceSession()
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        session = self.sessions.get(session_id)
        if session and session.is_expired():
            del self.sessions[session_id]
            return None
        return session
    
    def link_openclaw_session(self, voice_id: str, openclaw_id: str):
        self.openclaw_mapping[voice_id] = openclaw_id
        session = self.sessions.get(voice_id)
        if session:
            session.openclaw_session_id = openclaw_id
    
    def cleanup_expired(self):
        expired = [
            sid for sid, s in self.sessions.items() 
            if s.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Basic bidirectional flow

- [ ] Create new repo: `openclaw-voice-v2`
- [ ] Implement HTTP bridge to OpenClaw
- [ ] Add response filtering (heuristic fallback)
- [ ] Integrate existing STT (Faster-Whisper) + TTS (Piper)
- [ ] Basic session management
- [ ] Push-to-talk mode only

**Deliverable:** Voice input → OpenClaw → Voice output workflow

### Phase 2: Intelligence (Week 3-4)
**Goal:** Smart filtering + wake word

- [ ] OpenClaw plugin for metadata tagging
- [ ] Move from heuristic to metadata-based filtering
- [ ] Integrate wake word detection (Porcupine/OpenWakeWord)
- [ ] Hands-free activation
- [ ] Session persistence across turns

**Deliverable:** "Hey Hal, what's on my calendar?" → spoken response

### Phase 3: Fluidity (Week 5-6)
**Goal:** Natural conversation flow

- [ ] WebSocket implementation for lower latency
- [ ] Interruption handling (barge-in)
- [ ] Streaming TTS (start speaking before full response)
- [ ] Conversation context (multi-turn memory)
- [ ] Error recovery and fallbacks

**Deliverable:** Fluid multi-turn conversations with interruptions

### Phase 4: Polish (Week 7-8)
**Goal:** Production-ready experience

- [ ] Voice activity detection (VAD) for natural endpointing
- [ ] Voice cloning for personalized assistant voice
- [ ] Multi-language support
- [ ] Configuration UI/web interface
- [ ] Performance optimization

**Deliverable:** Daily-driver voice interface

---

## GitHub Repository Structure

### V2 Repository: `openclaw-voice-v2`

```
openclaw-voice-v2/
├── README.md                     # Project overview
├── LICENSE                       # Apache 2.0
├── .gitignore
│
├── docs/                         # Documentation
│   ├── architecture.md           # Detailed system design
│   ├── api-reference.md            # OpenClaw integration API
│   ├── configuration.md            # Setup guide
│   └── troubleshooting.md          # Common issues
│
├── src/                          # Source code
│   ├── bridge/                   # Core bridge modules
│   │   ├── __init__.py
│   │   ├── openclaw_client.py     # HTTP/WebSocket client
│   │   ├── session_manager.py     # Session persistence
│   │   └── response_filter.py     # Filtering logic
│   │
│   ├── audio/                    # Audio pipeline
│   │   ├── __init__.py
│   │   ├── capture.py             # Microphone input
│   │   ├── stt_engine.py          # Whisper integration
│   │   ├── tts_engine.py          # Piper integration
│   │   └── playback.py            # Audio output
│   │
│   ├── wake/                     # Wake word detection
│   │   ├── __init__.py
│   │   ├── porcupine_wake.py      # Porcupine integration
│   │   └── openwakeword_wake.py   # OpenWakeWord fallback
│   │
│   ├── vad/                      # Voice Activity Detection
│   │   ├── __init__.py
│   │   └── silero_vad.py          # Silero VAD
│   │
│   ├── config/                   # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py            # Pydantic settings
│   │   └── default_config.yaml
│   │
│   └── main.py                   # Entry point
│
├── plugins/                      # OpenClaw plugins
│   └── response_filter_plugin.py  # Metadata tagging
│
├── tests/                        # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/                      # Utility scripts
│   ├── install.sh                # Installation script
│   ├── setup-venv.sh             # Environment setup
│   └── download-models.sh        # Model downloader
│
├── docker/                       # Container support
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── examples/                     # Example configs & tests
    ├── openclaw-config.yaml
    └── voice-config.yaml
```

### V1 Preserved

Keep `ray1caron/local-voice` intact as reference and fallback.

### Branching Strategy

```
main                    ← Stable releases (v2.0.x, v2.1.x)
├── develop            ← Integration branch
│   ├── feature/websocket
│   ├── feature/wake-word
│   └── feature/interruptions
├── release/v2.0.0
└── hotfix/*
```

---

## GitHub Projects Setup

### Sprint Board: "Voice Interface v2 Development"

**Columns:**
1. 📋 Backlog
2. 🔄 Ready
3. 🏃 In Progress
4. 👀 Code Review
5. ✅ Done

### Milestones

| Milestone | Target Date | Focus |
|-----------|-------------|-------|
| v2.0-alpha | Week 2 | Basic bidirectional flow |
| v2.0-beta | Week 4 | Wake word + filtering |
| v2.0.0 | Week 6 | WebSocket + interruptions |
| v2.1.0 | Week 8 | Polish + VAD |

### Label System

- `priority:critical` - Blocker
- `priority:high` - Important
- `priority:medium` - Nice to have
- `priority:low` - Future
- `type:bug` - Bug fix
- `type:feature` - New feature
- `component:stt` - Speech-to-text
- `component:tts` - Text-to-speech
- `component:bridge` - OpenClaw bridge
- `component:filter` - Response filtering
- `area:perf` - Performance
- `area:security` - Security

---

## Edge Cases & Mitigations

| Edge Case | Scenario | Mitigation |
|-----------|----------|------------|
| **Interruption** | User speaks while assistant is speaking | VAD detects new speech → send `interruption` signal to OpenClaw → cancel TTS queue → process new input |
| **Long responses** | Tool chain produces 500+ tokens | Stream TTS incrementally; use sentence boundaries to chunk |
| **STT errors** | Whisper returns gibberish | Confidence threshold (>0.6); ask user to repeat |
| **Network failure** | OpenClaw unreachable | Queue locally; friendly voice error: "I'm having trouble connecting" |
| **Session timeout** | 30min silence | Graceful shutdown; wake word restarts new session |
| **Tool output filtering** | `exec` returns 1000 lines | Summarize before TTS: "I found 12 results, here are the top 3" |
| **Multi-turn context** | "What about yesterday?" | Session manager retains history; inject into OpenClaw context |
| **Wake word false positive** | TV says "Hey Hal" | Secondary confirmation or speaker identification |
| **Concurrent sessions** | Multiple users, one OpenClaw | Session isolation; user-specific voice profiles |

---

## Configuration Reference

### voice-config.yaml

```yaml
# Core settings
session:
  ttl_minutes: 30
  max_history: 10
  save_path: "~/.openclaw-voice/sessions"

# OpenClaw connection
openclaw:
  host: "localhost"
  port: 3000
  protocol: "websocket"  # or "http"
  api_version: "v1"
  
  # Integration settings
  response_filtering:
    mode: "metadata"     # or "heuristic"
    include_thinking: false
    include_tool_calls: false
  
  # Session linking
  session_mapping: true  # Link voice sessions to OpenClaw sessions

# Audio pipeline
audio:
  input:
    device: "default"
    sample_rate: 16000
    channels: 1
    chunk_size: 1024
  
  output:
    device: "default"
    volume: 0.8
    
  # Voice Activity Detection
  vad:
    enabled: true
    engine: "silero"     # or "webrtc"
    threshold: 0.5
    min_speech_duration_ms: 250
    min_silence_duration_ms: 500

# Speech-to-Text
stt:
  engine: "whisper"
  model: "medium"        # tiny, base, small, medium, large-v3
  device: "cuda"         # cuda, cpu
  compute_type: "float16"
  language: "en"
  
# Text-to-Speech
tts:
  engine: "piper"
  model: "en_US-amy-medium"
  speed: 1.0
  
  streaming:
    enabled: true
    sentence_chunking: true

# Wake Word
wake_word:
  enabled: true
  engine: "porcupine"    # or "openwakeword"
  
  porcupine:
    access_key: "${PICOVOICE_KEY}"  # env var
    keywords: ["computer", "jarvis"]
    sensitivity: 0.7
  
  openwakeword:
    model: "hey_hal"
    threshold: 0.5

# Conversation
conversation:
  barge_in:
    enabled: true          # Allow interruptions
    sensitivity: "medium"  # low, medium, high
  
  pause_timeout: 3.0     # Seconds of silence before turn end
  max_response_length: 500  # Tokens before summarization
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Latency** | <2s end-to-end | Stopwatch: speech end → audio start |
| **Accuracy** | >95% STT | Manual evaluation of 100 phrases |
| **Availability** | >99% uptime | Session crash rate |
| **User Satisfaction** | >4/5 | Informal rating after use |
| **Context Retention** | 5+ turns | Multi-turn accuracy test |

---

## OpenClaw Integration Checklist

To enable this voice interface, OpenClaw needs:

- [ ] `/api/voice/chat` endpoint with SSE streaming
- [ ] WebSocket `/voice` endpoint for bidirectional
- [ ] `voice_mode` parameter to enable filtering
- [ ] Response metadata tags (`type: final`, `type: thinking`, etc.)
- [ ] Session ID linking between voice and main sessions
- [ ] Interruption signal handling (cancel ongoing generation)

---

## Next Actions

1. **Create Repository**: `ray1caron/openclaw-voice-v2`
2. **Setup GitHub Project**: Sprint board with milestones
3. **OpenClaw RFC**: Propose API changes for response tagging
4. **Phase 1 Kickoff**: Implement HTTP bridge + fallback filtering
5. **Testing**: Daily dogfooding with Ray's OpenClaw instance

---

## Configuration Architecture

### Configuration Sources (Priority Order)

```
Environment Variables → User Config (~/.config) → Default Config (repo) → Code Defaults
     (highest)            (user overrides)        (repository)         (fallbacks)
```

**Why this order:**
- **Env vars:** Secrets that shouldn't be in files (tokens, passwords)
- **User config ~/.config/voice-bridge-v2/:** Personal preferences (audio devices, voice settings)
- **Default config:** Sane defaults shipped with code
- **Code defaults:** Hardcoded fallbacks

### Key Configuration Decisions

| Decision | Rationale | Performance Impact |
|----------|-----------|-------------------|
| **Localhost OpenClaw** | Eliminates network latency | ✅ Critical for <2s target |
| **Minimal dependencies** | Reduce complexity | ✅ Manageable stack |
| **Config hot-reload** | Development convenience | ⚠️ ~1-2% CPU (dev only) |
| **XDG compliance** | Standard locations | ✅ No impact |
| **Audio name discovery** | Resilient to changes | ✅ One-time cost |
| **Env vars for secrets** | Security | ✅ No impact |

### Configuration Files

**Repository defaults:** `config/default.yaml`
```yaml
bridge:
  openclaw:
    host: "localhost"
    port: 3000
    secure: false

audio:
  sample_rate: 16000
  channels: 1

stt:
  model: "medium"
  device: "cuda"
  
secret_from_env: "${OPENCLAW_API_KEY}"
```

**User overrides:** `~/.config/voice-bridge-v2/config.yaml`
```yaml
audio:
  input_device: "USB Audio"
  output_device: "Built-in Audio"

wake:
  keyword: "Hal"

logging:
  level: "DEBUG"
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `VOICEBRIDGE_OPENCLAW_HOST` | OpenClaw server | `192.168.1.100` |
| `VOICEBRIDGE_OPENCLAW_API_KEY` | API authentication | `secret-token` |
| `GITHUB_TOKEN` | For issue creation | `ghp_...` |
| `VOICEBRIDGE_CONFIG_PATH` | Custom config location | `/etc/voice-bridge/` |
| `VOICEBRIDGE_LOG_LEVEL` | Runtime logging | `DEBUG` |

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **End-to-end latency** | <2s | Speech end → audio start |
| **STT latency** | 300-500ms | Whisper medium on CUDA |
| **LLM TTFB** | <500ms | Time to first byte |
| **TTS latency** | 200ms | Piper generation |
| **Audio pipeline** | <50ms | Capture/playback |
| **Tool query** | 3-4s | With tool execution |

---

## User Feedback System

### Why Feedback is Critical

When humans talk to computers, they need **state awareness** to know:
- When to speak (is it listening?)
- When to wait (is it thinking?)
- If they were understood (did it hear me?)
- If something went wrong (error state)

Without feedback, users experience:
- **Uncertainty** → "Did it hear me?"
- **Anxiety** → "Should I repeat?"
- **Frustration** → "Why isn't it responding?"
- **Over-talking** → Interrupting before response

### States to Communicate

1. **Idle** — Waiting for wake word
2. **Listening** — Capturing speech (after wake word)
3. **Thinking** — Processing (STT → OpenClaw → TTS)
4. **Speaking** — Playing response
5. **Error** — Something went wrong

### Implementation Options

#### Option 1: Audio Feedback Only (Earcons)

**States:**
- **Wake detected:** Ascending chime ("ding-dong")
- **Listening start:** Single beep
- **Listening end:** Double beep
- **Thinking:** Subtle hum (optional)
- **Speaking:** No tone (TTS plays)
- **Error:** Descending tone ("uh-oh")

**Pros:**
- ✅ Works without screen (headless-friendly)
- ✅ User doesn't need to look at anything
- ✅ Natural for voice-only interaction
- ✅ Low latency (<5ms)

**Cons:**
- ❌ Can interfere with speech if not careful
- ❌ Harder to convey complex state

**Best for:** Headless setups, voice-only interaction

#### Option 2: Visual Feedback Only

**States:**
```
🔴 Idle (waiting for wake word)
🟢 Listening (after wake word, capturing speech)
🔵 Thinking (processing, STT → OpenClaw → TTS)
⚪ Speaking (TTS playing)
🟡 Error (something went wrong)
```

**Implementation:**
- Desktop GUI window (tkinter/PyQt)
- System tray icon with color states
- LED control (if hardware available)
- Terminal status bar (for dev)

**Pros:**
- ✅ No audio interference with speech
- ✅ Clear visual hierarchy
- ✅ Can show detailed status

**Cons:**
- ❌ Requires screen
- ❌ User must look at screen

**Best for:** Desktop/laptop use with screen visible

#### Option 3: Combined Audio + Visual (Recommended)

**Implementation:**
- Visual indicator for primary state
- Audio earcons for state transitions only
- Detailed status in visual, simple cues in audio

**States:**
```
Visual: 🔴 Idle    Audio: (none)
Visual: 🟢 Listening    Audio: "ding" (wake detected)
Visual: 🔵 Thinking    Audio: (none, or subtle hum)
Visual: ⚪ Speaking    Audio: (none, TTS plays)
Visual: 🟡 Error    Audio: "uh-oh" tone
```

**Pros:**
- ✅ Best of both worlds
- ✅ Visual for detailed status
- ✅ Audio for immediate feedback
- ✅ Flexible (can disable audio if needed)

**Cons:**
- ❌ More complex to implement
- ❌ Requires both GUI and audio systems

**Best for:** General use, flexible deployment

### Performance Impact

| Metric | Without Feedback | With Feedback | Delta |
|--------|------------------|---------------|-------|
| CPU Usage | Baseline | +1-3% | Negligible |
| Memory | Baseline | +25MB | Acceptable |
| Latency | Baseline | +10-15ms | Negligible |
| User Experience | ❌ Uncertainty | ✅ Confidence | **Major improvement** |

### Best Practices Summary

1. **Immediate feedback** (<100ms) — Any user action gets instant response
2. **Progressive disclosure** — Simple state first, detail on demand
3. **Non-blocking** — Feedback doesn't prevent user action
4. **Consistent mapping** — Same state = same feedback every time
5. **Graceful degradation** — If visual fails, audio still works
6. **User control** — Can disable audio feedback if desired

### Recommended for Your Setup

**Phase 1 (MVP):** Audio + Terminal Status
- Audio earcons for state transitions
- Terminal status line for development
- Simple, no GUI dependencies

**Phase 2 (Enhancement):** Add Visual
- System tray icon
- Optional desktop widget
- LED support (if hardware added)

---

## Document References

- **FEEDBACK_DESIGN.md** — Full implementation guide with code examples
- **CONFIG_DISCUSSION.md** — Configuration architecture analysis
- **PROJECT.md** — Quick reference for development sessions
- **voice-assistant-plan-v2.md** — Main architecture document (this file)
