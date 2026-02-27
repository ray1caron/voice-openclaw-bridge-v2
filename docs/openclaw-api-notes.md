# OpenClaw API Notes

**Generated from:** `spike_openclaw.py` (Day 0 spike)
**Date:** 2026-02-27
**Purpose:** Document exact API shape for OpenClaw client implementation

---

## Gateway Configuration

```
Base URL: http://localhost:3000
Session ID: main
Timeout: 10s (default)
```

---

## API Endpoints

### 1. Health Check

**GET `/health`**

```bash
curl http://localhost:3000/health
```

**Response:** (to be populated by spike)

```json
{
  "status": "ok",
  "version": "x.x.x"
}
```

---

### 2. List Sessions

**GET `/api/sessions`**

```bash
curl http://localhost:3000/api/sessions
```

**Response:** (to be populated by spike)

```json
[
  {
    "sessionKey": "main",
    "model": "ollama/llama3.1:8b",
    "state": "active",
    "createdAt": "..."
  }
]
```

**Notes:**
- (Add notes after spike)

---

### 3. Send Message to Session

**POST `/api/sessions/{sessionKey}/send`**

```bash
curl -X POST http://localhost:3000/api/sessions/main/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, OpenClaw!"
  }'
```

**Request Body:**

```json
{
  "message": "string (required)",
  "timeoutSeconds": "number (optional, default 30)",
  "model": "string (optional, overrides default)"
}
```

**Response:** (to be populated by spike)

```json
{
  "success": true,
  "response": "Hello! How can I help you?",
  "model": "ollama/llama3.1:8b",
  "latencyMs": 1234,
  "toolCalls": [],
  "reasoning": false
}
```

**Error Responses:**

```json
// 404 Session not found
{
  "error": "Session not found",
  "sessionKey": "unknown"
}

// 400 Invalid request
{
  "error": "Invalid message",
  "details": "Message cannot be empty"
}
```

**Notes:**
- (Add notes after spike about synchronous vs async)
- (Document streaming behavior if applicable)

---

### 4. Get Session Output (if supported)

**GET `/api/sessions/{sessionKey}/output?since={timestamp}`**

```bash
curl "http://localhost:3000/api/sessions/main/output?since=0"
```

**Response:** (to be populated by spike - may return 404 if unsupported)

```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "Hello!",
      "timestamp": 1690000000000
    }
  ],
  "lastTimestamp": 1690000000000
}
```

**Notes:**
- This endpoint may not exist in all OpenClaw versions
- Alternative: responses come synchronously in POST body

---

## Message Types

### Incoming (from OpenClaw)

```json
{
  "message": "The actual response text",
  "metadata": {
    "messageType": "final|thinking|tool_call|tool_result",
    "model": "ollama/llama3.1:8b",
    "latencyMs": 1234,
    "tokenCount": 45,
    "reasoning": false
  },
  "toolCalls": [
    {
      "tool": "web_search",
      "parameters": {"query": "..."},
      "result": "..."
    }
  ]
}
```

**Message Types:**
- `final`: Complete response ready to speak
- `thinking`: Internal reasoning (don't speak)
- `tool_call`: Tool is being executed (don't speak)
- `tool_result`: Tool execution result (don't speak)

---

## Client Implementation Guidance

### Class Structure

```python
class OpenClawClient:
    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        session_key: str = "main",
        timeout: float = 30.0
    ):
        self.base_url = base_url
        self.session_key = session_key
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    async def send_message(
        self,
        message: str,
        timeout_seconds: float | None = None
    ) -> OpenClawResponse:
        """Send message to OpenClaw and get response."""
        pass

    async def list_sessions(self) -> list[SessionInfo]:
        """List all active sessions."""
        pass

    def health_check(self) -> bool:
        """Check if gateway is running."""
        pass

    def close(self):
        """Close HTTP client."""
        self.client.close()
```

### Error Handling

```python
try:
    response = await client.send_message("Hello")
except httpx.ConnectError:
    # Gateway not running
    logger.error("Cannot connect to OpenClaw gateway")
    raise
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        # Session not found
        logger.error(f"Session {session_key} not found")
        raise
    elif e.response.status_code == 400:
        # Invalid request
        logger.error(f"Invalid request: {e.response.text}")
        raise
    else:
        # Other HTTP error
        raise
except httpx.TimeoutException:
    # Request timed out
    logger.error(f"Request timed out after {timeout}s")
    raise
```

### Response Filtering

Use the `messageType` metadata to decide what to speak:

```python
def is_speakable(response: OpenClawResponse) -> bool:
    """Check if response should be spoken by TTS."""
    message_type = response.metadata["messageType"]

    # Only speak final responses
    if message_type == "final":
        return True

    # Don't speak thinking, tool calls, or tool results
    return False
```

---

## Integration with Response Filter

The ResponseFilter (Sprint 1) already handles filtering logic. We'll feed OpenClaw responses into it:

```python
from bridge.response_filter import ResponseFilterManager

# Create filter manager
filter_manager = ResponseFilterManager()

# After getting OpenClaw response
if filter_manager.should_speak(response["message"], response["metadata"]):
    # Speak it
    await tts_worker.speak(response["message"])
else:
    # Log but don't speak (thinking, tool calls)
    logger.info("Response filtered", metadata=response["metadata"])
```

---

## Configuration Changes

Add to `config.yaml`:

```yaml
openclaw:
  host: localhost
  port: 3000
  http_base_url: http://localhost:3000
  session_key: main
  timeout: 30.0
  retry_on_failure: true
  max_retries: 3
```

---

## Testing

### Unit Tests (`tests/unit/test_openclaw_client.py`)

```python
import pytest
from bridge.openclaw_client import OpenClawClient

def test_health_check(mocker):
    """Test gateway health check."""
    client = OpenClawClient()
    assert client.health_check() == True

def test_send_message(mocker):
    """Test sending message."""
    mock_response = {
        "message": "Hello!",
        "metadata": {"messageType": "final"}
    }

    mocker.patch('httpx.post', return_value=mock_response)

    client = OpenClawClient()
    response = await client.send_message("Hello")
    assert response["message"] == "Hello!"

def test_session_not_found(mocker):
    """Test 404 error handling."""
    mocker.patch('httpx.post', side_effect=httpx.HTTPStatusError(...))

    client = OpenClawClient()
    with pytest.raises(OpenClawError):
        await client.send_message("Hello")
```

### Integration Tests (`tests/integration/test_openclaw_integration.py`)

```python
async def test_real_openclaw_connection():
    """Test actual connection to running OpenClaw."""
    client = OpenClawClient()
    response = await client.send_message("ping")
    assert response is not None
```

---

## Questions to Resolve During Spike

- [ ] Is `/api/session/{key}/send` the correct endpoint?
- [ ] Are responses synchronous or async?
- [ ] What fields are in the response metadata?
- [ ] Is there a streaming endpoint for long responses?
- [ ] How are tool calls represented in the response?
- [ ] What's the default session key?
- [ ] Is authentication required?

---

## Update Log

| Date | Change | Who |
|------|--------|-----|
| 2026-02-27 | Initial template | Hal |
| (fill in after spike) | API shape documented | Hal |

---

## References

- [OpenClaw Docs](https://docs.openclaw.ai)
- [HTTP API spec](https://docs.openclaw.ai/api) (location TBD)
- VOICE_BRIDGE_V2_IMPLEMENTATION_PLAN_V2.md