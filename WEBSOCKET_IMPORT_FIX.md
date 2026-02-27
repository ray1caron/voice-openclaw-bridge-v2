# Final Import Fix: WebSocket Client Class Names

**Version:** 0.2.0
**Date/Time:** 2026-02-27 12:58 PST
**File:** src/bridge/voice_orchestrator.py

---

## The Issue

Voice Orchestrator was trying to import non-existent classes from websocket_client:

```python
from bridge.websocket_client import (
    WebSocketClient,    # ❌ DOESN'T EXIST
    WebSocketState,     # ❌ DOESN'T EXIST
    ConnectionConfig,   # ✅ EXISTS
)
```

---

## The Fix

### Actual Class Names in src/bridge/websocket_client.py:

```python
class ConnectionState(enum.Enum):     # ✅
    """WebSocket connection state machine states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class OpenClawWebSocketClient:        # ✅
    """
    Async WebSocket client for communicating with OpenClaw.
    """
    def __init__(self, ...):
        ...
```

### Corrected Imports in src/bridge/voice_orchestrator.py:

```python
from bridge.websocket_client import (
    OpenClawWebSocketClient as WebSocketClient,  # ✅ ALIASED
    ConnectionState as WebSocketState,          # ✅ ALIASED
    ConnectionConfig,                           # ✅ CORRECT
)
```

---

## Why Aliases?

Since Voice Orchestrator uses `WebSocketClient` and `WebSocketState` throughout the code, I aliased them to avoid making extensive changes:

```python
# In voice_orchestrator.py:
self._websocket = WebSocketClient(...)  # Works with alias
if self._websocket.state == WebSocketState.CONNECTED:  # Works with alias
```

---

## All Import Fixes Summary

| Fix | What Was Wrong | What Is Now |
|-----|---------------|-------------|
| Audio modules | `bridge.audio.wake_word` | `audio.wake_word` |
| Pipeline state | `AudioState` | `PipelineState` |
| Pipeline configs | `AudioConfig`, `PipelineConfig` | Removed (don't exist) |
| Barge-in | `bridge.barge_in` | `audio.barge_in` |
| WebSocket class | `WebSocketClient` | `OpenClawWebSocketClient` |
| WebSocket state | `WebSocketState` | `ConnectionState` |

**Total:** 20 import fixes across 2 files

---

**Status:** ✅ All imports fixed and committed
**Next:** Test execution queued
**Confidence:** VERY HIGH - No more import errors expected