# Gateway Discovery & Spike Update

**Date:** 2026-02-27 10:15 PST
**Status:** ✅ OpenClaw gateway found and documented

---

## Discovery Results

### Gateway Running ✅

```
Gateway: OpenClaw
Status: Active
Port: 18789 (NOT 3000!)
Bind: 127.0.0.1 (loopback only)
Auth: Bearer token required
Dashboard: http://127.0.0.1:18789/
```

### Key Findings

1. **Wrong Port in Original Plan**
   - Impl. plan assumed: `localhost:3000`
   - Actual port: `127.0.0.1:18789`
   - Updated in: all config and spike files

2. **Authentication Required**
   - Mode: Bearer token
   - Token location: `~/.openclaw/openclaw.json` → `gateway.auth.token`
   - Token: `2fb4459127f320829acfd1b14b0174dd8358d6eb02d141f9`

3. **Local Mode**
   - Bound to localhost only (good security)
   - No external exposure
   - Dashboard available at http://127.0.0.1:18789/

---

## Files Updated

### 1. `spike_openclaw.py` - Updated for Real Gateway

**Changes:**
- Default URL: `http://127.0.0.1:18789` (was 3000)
- Added Bearer token authentication
- Token hardcoded for spike: `2fb4459127f320829acfd1b14b0174dd8358d6eb02d141f9`
- All HTTP calls now include `Authorization: Bearer <token>` header

**Functions updated:**
- `test_health()` ✅
- `test_list_sessions()` ✅
- `test_send_message()` ✅
- `test_get_session_output()` ✅

### 2. `docs/OPENCLAW_GATEWAY_FINDINGS.md` - NEW

Complete documentation of:
- Gateway configuration
- API endpoints (with auth)
- Security considerations
- Updated config recommendations
- Next steps

### 3. `config.example.yaml` - NEW

Updated configuration with:
- Correct port: 18789
- Auth token field
- All sections documented
- Ready to copy to `~/.voice-bridge/config.yaml`

---

## Ready to Run Spike

### Command:
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
python3 spike_openclaw.py
```

### What It Tests:
1. ✅ Gateway health check (`/health`)
2. ✅ List sessions (`/api/sessions`)
3. ✅ Send message (`/api/sessions/main/send`)
4. ✅ Get output (`/api/sessions/main/output` - optional)

### Expected Output (if works):
```
============================================================
  Step 1: Gateway Health Check
============================================================
Connecting to: http://127.0.0.1:18789

✅ Gateway is UP
   Status: 200
   Response: {...}

============================================================
  Step 2: List Sessions
============================================================
GET http://127.0.0.1:18789/api/sessions

✅ Sessions retrieved
   Count: N

============================================================
  Step 3: Send Test Message
============================================================
POST http://127.0.0.1:18789/api/sessions/main/send
Session ID: main
Message: 'ping'

✅ Message sent successfully
   Response: {...}

============================================================
  ✅ SPIKE PASSED
============================================================
OpenClaw gateway is accessible and sessions API works!

Next steps:
  1. Document exact API shape in docs/openclaw-api-notes.md
  2. Create src/bridge/openclaw_client.py with HTTP client
  3. Integrate with audio pipeline for full voice loop
```

---

## Configuration to Apply

After spike passes, create real config:

```bash
mkdir -p ~/.voice-bridge
cp config.example.yaml ~/.voice-bridge/config.yaml

# Edit to match your setup
nano ~/.voice-bridge/config.yaml
```

**Key things to set:**
- `audio.input_device` - Your microphone
- `audio.output_device` - Your speakers
- `stt.model` - Whisper model size (base/small/medium)
- `tts.voice` - Piper voice model

Run discovery to find devices:
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
python3 -m bridge.audio_discovery
```

---

## Next Steps After Spike Passes

### Day 1: OpenClaw HTTP Client
1. Create `src/bridge/openclaw_client.py`
2. Implement with:
   - Bearer token auth
   - Port 18789
   - Error handling
3. Write tests: `tests/unit/test_openclaw_client.py`

### Day 2-3: STT/TTS Integration
1. Create `src/audio/stt_worker.py` (Whisper)
2. Create `src/audio/tts_worker.py` (Piper)
3. Connect to OpenClaw client
4. End-to-end audio pipeline

### Day 4-6: Polish
1. Wake word detection
2. State machine
3. System tests
4. Demo: "Hey Hal, what time is it?"

---

## Alternatives Considered

### Option A: HTTP API (Current Plan)
- ✅ Simple, well-understood
- ✅ Easy to test
- ✅ Auth documented
- ⚠️ Add HTTP overhead (~50-100ms)

### Option B: WebSocket Direct
- ✅ Lower latency
- ✅ Existing `websocket_client.py` (53 tests)
- ✅ Bidirectional streaming
- ❓ Need to verify WebSocket protocol

### Recommendation
- Use HTTP API for Day 1-2 (simple, proven)
- Consider WebSocket migration Day 4-6 (for streaming TTS)

---

## Blockers Removed

- ✅ Gateway not accessible → Gateway found on port 18789
- ✅ Unknown port → Port documented and configured
- ✅ Auth unknown → Bearer token from config
- ⏸️ API shape → Pending spike execution

---

## Executive Summary

**Before:**
- Thought OpenClaw on port 3000
- No auth info
- Spike pointing to wrong gateway

**After:**
- ✅ Gateway found: 127.0.0.1:18789
- ✅ Auth documented: Bearer token
- ✅ Spike updated and ready
- ✅ Config template created

**What Changed:**
- 1 port number (3000 → 18789)
- +4 auth headers (Bearer token)
- +2 documentation files
- +1 config template

**Time to Complete:** ~15 minutes (doc, update, create)
**Ready for:** Spike execution (pending approval)

---

**Updated:** 2026-02-27 10:15 PST
**Status:** Spike ready, awaiting execution
**Next:** Run `python3 spike_openclaw.py` once approved