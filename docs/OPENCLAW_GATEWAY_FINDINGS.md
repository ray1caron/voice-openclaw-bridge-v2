# OpenClaw Gateway Discovery

**Date:** 2026-02-27
**Status:** Gateway running, API documented

---

## Gateway Status

```
✅ Running
✅ Port: 18789 (not 3000!)
✅ Mode: local (loopback only)
✅ Auth: token-based
```

---

## Gateway Configuration

From `~/.openclaw/openclaw.json`:

```json
{
  "gateway": {
    "auth": {
      "mode": "token",
      "token": "2fb4459127f320829acfd1b14b0174dd8358d6eb02d141f9"
    },
    "bind": "loopback",
    "mode": "local",
    "port": 18789
  }
}
```

**Key Points:**
- Port is **18789**, not 3000
- Requires **Bearer token** authentication
- Bound to localhost only (127.0.0.1)
- Dashboard at: http://127.0.0.1:18789/

---

## API Endpoints (To be verified)

Based on OpenClaw architecture:

### Authentication
**Required for all API calls:**

```bash
curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:18789/api/...
```

Where `<TOKEN>` is from `~/.openclaw/openclaw.json` → `gateway.auth.token`

### Health / Status
```
GET /health
GET /status
GET /api/health
```

### Sessions
```
GET /api/sessions
GET /api/sessions/:sessionKey
POST /api/sessions/:sessionKey/send
GET /api/sessions/:sessionKey/history
POST /api/sessions
DELETE /api/sessions/:sessionKey
```

### Spawn Sessions
```
POST /api/sessions/spawn
Content-Type: application/json

{
  "task": "your task",
  "model": "ollama/llama3.2:3b",
  "session": true
}
```

### Message Send
```
POST /api/sessions/:sessionKey/send
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "your message",
  "timeoutSeconds": 30
}
```

---

## Updated Spike Configuration

**Correct URL:** http://127.0.0.1:18789
**Auth Required:** Yes (Bearer token)

Updated command:
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
# Need to update spike to use token auth
python3 spike_openclaw.py http://127.0.0.1:18789
```

---

## Configuration Update for Voice Bridge

Add to `~/.voice-bridge/config.yaml`:

```yaml
openclaw:
  # HTTP API endpoint
  http_base_url: "http://127.0.0.1:18789"
  api_key: "2fb4459127f320829acfd1b14b0174dd8358d6eb02d141f9"

  # WebSocket endpoint (bypasses HTTP API)
  ws_url: "ws://127.0.0.1:18789"

  # Session configuration
  session_key: "main"
  default_model: "ollama/glm-4.7:cloud"

  # Timeouts
  connect_timeout: 5.0
  request_timeout: 30.0
  response_timeout: 60.0
```

---

## Security Considerations

**⚠️ Token Storage:**
- The auth token is in `~/.openclaw/openclaw.json`
- Should be referenced, not copied, to stay in sync
- Environment variable option: `OPENCLAW_AUTH_TOKEN`

**⚠️ Firewall:**
- Gateway is loopback-only (localhost only)
- Good security posture for local voice assistant
- No external exposure

---

## Next Steps

1. **Update spike script** to:
   - Use correct port: 18789
   - Add Bearer token authentication
   - Test all endpoints

2. **Test API calls:**
   ```bash
   # Check auth
   curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:18789/api/sessions

   # Send simple message
   curl -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message":"ping"}' \
     http://127.0.0.1:18789/api/sessions/main/send
   ```

3. **Update voice bridge config:**
   - Change port from 3000 to 18789
   - Add auth token configuration
   - Test with real OpenClaw connection

4. **Alternative: WebSocket Integration**
   - The existing `websocket_client.py` already handles WebSocket
   - May avoid HTTP API altogether
   - Investigate WebSocket message protocol

---

## Questions Resolved

- ✅ Gateway running? Yes, port 18789
- ✅ Auth required? Yes, Bearer token
- ✅ Token accessible? Yes, in config file
- ❓ API endpoints? Still need to verify via actual tests
- ❓ WebSocket vs HTTP? WebSocket client already exists

---

## Blockers Removed

- ❌ ~~Gateway not accessible~~ → ✅ Running on 18789
- ❌ ~~Port unknown~~ → ✅ Configured as 18789
- ❌ ~~Auth method~~ → ✅ Bearer token documented

**Remaining:**
- ⏸️ Actual API verification (pending exec approval)
- ⏸️ Full endpoint discovery

---

**Updated:** 2026-02-27 10:15 PST
**Status:** Gateway running, ready for API testing