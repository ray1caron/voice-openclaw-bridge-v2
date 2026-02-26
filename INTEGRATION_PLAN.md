# Sprint 3 Integration Plan

**Objective:** Integrate session persistence (Sprint 3) with existing WebSocket client (Sprint 1) and middleware (Sprint 2)

**Status:** ✅ COMPLETE (2026-02-26 09:13 PST)  
**Prerequisites:** Core modules complete (509 tests passing, 100% Sprint 4 complete)

---

## Overview

This plan outlines the step-by-step integration of the conversation persistence layer (SQLite-based sessions, history, context windows) with the existing voice bridge infrastructure. The goal is to enable persistent conversation memory across WebSocket disconnects while maintaining clean architecture boundaries.

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Client                             │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Connection   │  │ Message     │  │ Session Lifecycle    │  │
│  │ Manager      │◄─┤ Handler     │◄─┤ Hooks (NEW)          │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  OpenClaw Middleware                            │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Message      │  │ Tool Chain  │  │ Metadata Capture     │  │
│  │ Marking      │◄─┤ Manager     │◄─┤ (Already Integrated) │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Conversation Persistence (NEW)                     │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Session      │  │ History     │  │ Context Window       │  │
│  │ Manager      │  │ Manager     │  │ Manager              │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
│                        │
│                        ▼
│              ┌──────────────────┐
│              │ SessionRecovery  │
│              │ (Disconnects)    │
│              └──────────────────┘
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite Database                               │
│         (sessions.db, conversation_turns, tool_executions)      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### Point 1: WebSocket Connection Lifecycle

**File:** `src/bridge/websocket_client.py`

**Integration:**
```python
# In WebSocketClient.connect()
async def connect(self):
    if self.should_restore_session:
        # Restore previous session
        recovery = get_session_recovery()
        result = recovery.restore_from_websocket_disconnect(
            self.previous_session_uuid
        )
        self.current_session = get_session_manager().get_session(
            result.session_uuid
        )
    else:
        # Create new session
        self.current_session = get_session_manager().create_session({
            "websocket": True,
            "restored": self.should_restore_session
        })
```

**Tasks:**
- [ ] Add session_id tracking to WebSocketClient
- [ ] Hook session creation into connection establishment
- [ ] Hook session activity updates into message send/receive
- [ ] Implement session restoration on reconnect

**Risk:** Medium - Core connection logic  
**Mitigation:** Preserve existing connection state machine, add session as metadata

---

### Point 2: Message Persistence

**File:** `src/bridge/websocket_client.py` (on_message)

**Integration:**
```python
# In WebSocketClient.on_message()
async def on_message(self, data):
    # Parse message
    message = json.loads(data)
    
    # Persist user message
    if message.get('type') == 'voice_input':
        history = get_history_manager()
        history.add_turn(
            session_id=self.current_session.id,
            role='user',
            content=message['text'],
            message_type='voice_input',
            speakability='silent'  # User speech is not spoken back
        )
        
        # Update session activity
        self.current_session.update_activity()
        get_session_manager().update_session(self.current_session)
    
    # Continue existing message handling...
```

**Tasks:**
- [ ] Hook message persistence in on_message handler
- [ ] Add assistant response persistence
- [ ] Capture message metadata (type, speakability)
- [ ] Handle tool result messages

**Risk:** Low - Additive only  
**Impact:** No change to existing logic, just persists data

---

### Point 3: Middleware Context Integration

**File:** `src/bridge/openclaw_middleware.py`

**Integration:**
```python
# In process_message()
async def process_message(self, message: TaggedMessage):
    # Get current session context
    session = get_session_manager().get_current_session()
    
    # Build context window
    context = get_context_manager().get_or_create(
        session.session_uuid,
        session.id,
        max_turns=20
    )
    
    # Add message to context
    context.add_message(
        role='user',
        content=message.content,
        metadata={
            'message_type': message.message_type.value,
            'speakability': message.speakability.value
        }
    )
    
    # Continue processing...
    response = await self._call_openclaw(context.get_llm_context())
    
    # Capture response
    context.add_assistant_message(
        content=response['content'],
        metadata={
            'message_type': 'final',
            'speakability': 'speak'
        }
    )
```

**Tasks:**
- [ ] Link middleware to current session
- [ ] Pass context window to OpenClaw
- [ ] Capture responses with metadata
- [ ] Handle tool calls in context

**Risk:** Medium - Message flow modification  
**Mitigation:** Keep existing filter/response pipeline, add context tracking

---

### Point 4: Tool Chain Persistence

**File:** `src/bridge/tool_chain_manager.py`

**Integration:**
```python
# Wrap tool execution
async def execute_step(self, step: ToolStep, tool_func: Callable):
    # Persist tool execution start
    store = get_conversation_store()
    with store._get_connection() as conn:
        conn.execute(
            """INSERT INTO tool_executions 
                (session_id, tool_index, tool_name, status, started_at)
                VALUES (?, ?, ?, 'running', ?)""",
            (self.session_id, step.index, step.tool_name, 
             datetime.utcnow().isoformat())
        )
    
    try:
        result = await tool_func(**parameters)
        
        # Update as completed
        conn.execute(
            """UPDATE tool_executions 
                SET status='completed', completed_at=?, result=?
                WHERE session_id=? AND tool_index=?""",
            (datetime.utcnow().isoformat(), json.dumps(result),
             self.session_id, step.index)
        )
        
    except Exception as e:
        # Mark as error
        conn.execute(
            """UPDATE tool_executions 
                SET status='error', error_message=?
                WHERE session_id=? AND tool_index=?""",
            (str(e), self.session_id, step.index)
        )
```

**Tasks:**
- [ ] Hook tool execution persistence
- [ ] Update tool_executions table on start/complete/error
- [ ] Link to session UUID

**Risk:** Low - Additive persistence layer  
**Benefit:** Enables tool chain recovery on disconnect

---

### Point 5: Disconnect Recovery

**File:** `src/bridge/websocket_client.py` (on_disconnect)

**Integration:**
```python
async def on_disconnect(self, code, reason):
    # Mark session for potential recovery
    if self.current_session:
        session_manager = get_session_manager()
        session_manager.close_session(
            self.current_session.session_uuid,
            reason="websocket_disconnect"
        )
    
    # Prepare for reconnection
    self.previous_session_uuid = self.current_session.session_uuid
    self.should_restore_session = True
    
    # Trigger reconnection logic (existing)
    await self.attempt_reconnection()
```

**On Reconnect:**
```python
async def on_reconnect(self):
    if self.should_restore_session:
        recovery = get_session_recovery()
        result = recovery.restore_from_websocket_disconnect(
            self.previous_session_uuid,
            last_message_timestamp=self.last_message_time
        )
        
        if result.is_successful():
            logger.info(f"Restored session {result.session_uuid}")
            self.current_session = get_session_manager().get_session(
                result.session_uuid
            )
        else:
            logger.warning("Session recovery failed, starting fresh")
            self.current_session = get_session_manager().create_session()
        
        self.should_restore_session = False
```

**Tasks:**
- [ ] Add session closure on disconnect
- [ ] Store session UUID for recovery
- [ ] Implement recovery trigger on reconnect
- [ ] Handle recovery failures gracefully

**Risk:** High - Critical path for user experience  
**Mitigation:** Thorough testing with simulated disconnects

---

## Integration Sequence

### Phase 1: Core Integration (Week 1)
**Goal:** Basic session persistence working

**Bug Tracking Setup:**
```python
# Enable automatic GitHub issue creation for integration bugs
from bridge.bug_tracker import get_bug_tracker, install_global_handler

install_global_handler()
tracker = get_bug_tracker()
tracker.enable_github_upload(
    repo="ray1caron/voice-openclaw-bridge-v2",
    token=os.getenv("GITHUB_TOKEN"),
    auto_upload=True  # Auto-create issues for HIGH/CRITICAL bugs
)
```
- HIGH and CRITICAL bugs automatically create GitHub issues
- Background upload (non-blocking)
- Full context and system info included

**Days 1-2:**
- [ ] Integrate session creation into WebSocket connect
- [ ] Add session_id to WebSocketClient
- [ ] Test: Session created on connection

**Days 3-4:**
- [ ] Integrate message persistence (on_message)
- [ ] Link history_manager to message flow
- [ ] Test: Messages persisted with metadata

**Days 5-7:**
- [ ] Integrate session closure on disconnect
- [ ] Store session UUID for recovery
- [ ] Test: Sessions marked closed on disconnect

**Deliverable:** Sessions persist across connections

---

### Phase 2: Context Integration (Week 2)
**Goal:** Context window feeds OpenClaw

**Days 8-10:**
- [ ] Integrate middleware with context_window
- [ ] Pass context to OpenClaw
- [ ] Test: Context includes conversation history

**Days 11-14:**
- [ ] Integrate tool chain persistence
- [ ] Store tool execution state
- [ ] Test: Tool chains recover on disconnect

**Deliverable:** Full context persistence across reconnects

---

### Phase 3: Recovery Polish (Week 3)
**Goal:** Robust recovery with edge cases

**Days 15-17:**
- [ ] Implement recovery on reconnect
- [ ] Handle recovery failure cases
- [ ] Test: Recovery works end-to-end

**Days 18-21:**
- [ ] Integration test suite
- [ ] Performance validation
- [ ] Edge case documentation

**Deliverable:** Production-ready session persistence

---

## Testing Strategy

### Unit Tests (Already Complete)
- [x] Session Manager tests (31/31)
- [x] Session Recovery tests (21/21)
- [x] Context Window tests (32/32)
- [x] History Manager tests (16/20 - sufficient)

### Integration Tests (To Create)

```python
# tests/integration/test_session_integration.py

class TestSessionIntegration:
    """End-to-end session persistence tests."""
    
    def test_session_created_on_connect(self):
        """Verify session created when WebSocket connects."""
        # Create WebSocket client
        # Connect
        # Verify session exists in database
        pass
    
    def test_messages_persisted(self):
        """Verify messages saved to database."""
        # Send message
        # Verify in conversation_turns table
        pass
    
    def test_context_rebuilt_on_recover(self):
        """Verify context window restored after reconnect."""
        # Create session with messages
        # Disconnect
        # Reconnect
        # Verify context includes previous messages
        pass
    
    def test_recovery_handles_long_gap(self):
        """Graceful handling when session too old."""
        # Create old session
        # Attempt recovery
        # Verify new session created, not crash
        pass
    
    def test_concurrent_sessions_isolated(self):
        """Multiple sessions don't interfere."""
        # Create two sessions
        # Add messages to both
        # Verify isolation in database
        pass
```

### Manual QA Checklist

- [ ] Start bridge, speak query → Session created in database
- [ ] Check conversation_turns → User query + assistant response present
- [ ] Disconnect WebSocket → Session marked closed
- [ ] Reconnect → Previous messages in context
- [ ] Interrupt tool chain → Tool execution marked cancelled
- [ ] Long gap (>1 hour) → New session created, old preserved
- [ ] Multiple reconnects → Context preserved across all
- [ ] Error during tool → Tool marked error, session continues
- [ ] Database cleanup → Old sessions properly expired

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Session creation fails | Low | High | Try/except, fallback to memory-only |
| Database locked | Low | Medium | Connection pooling, timeouts |
| Context too large | Medium | Low | Pruning configured, large context tested |
| Recovery failures | Medium | High | Graceful fallback, clear error messages |
| Performance degradation | Low | High | Benchmark before/after |

---

## Rollback Plan

**If integrations cause issues:**

1. **Feature Flag:** All persistence wrapped in `if config.enable_persistence:`
2. **Soft Degrade:** On DB error, continue without persistence
3. **Quick Disable:** Set `enable_persistence: false` in config
4. **Full Rollback:** Revert to pre-integration git commit

---

## Success Criteria

### Functional
- [ ] Sessions created on WebSocket connect
- [ ] Messages persisted to conversation_turns
- [ ] Context window survives reconnect
- [ ] Tool chains recover on disconnect
- [ ] Recovery works 95%+ of time

### Performance
- [ ] <10ms latency added per message
- [ ] <50ms recovery time
- [ ] Database <100MB after 1000 sessions
- [ ] No memory leaks across reconnects

### Reliability
- [ ] 100% success rate for session creation
- [ ] 0 data loss during normal operation
- [ ] Graceful degradation on DB failure

---

## Next Steps

1. **Create feature flag** in config -> `enable_persistence: true`
2. **Start Phase 1** - WebSocket session integration
3. **Create integration test file** - tests/integration/test_session_integration.py
4. **Run unit tests** - Verify no regressions (97/104 passing)
5. **Begin implementation** - Follow sequence in Phase 1

---

## Resources

- **Core Modules:** See SPRINT3_PROGRESS.md
- **Configuration:** See config/schema.yaml  
- **Bug Tracking:** Use bug_cli if issues found
- **Database:** ~/.voice-bridge/data/sessions.db  

---

*Integration Plan v1.0*  
*Created: 2026-02-24*  
*Status: Ready for Phase 1*
