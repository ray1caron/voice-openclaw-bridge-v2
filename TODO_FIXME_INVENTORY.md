# TODO/FIXME Inventory - Technical Debt

**Date:** 2026-02-28
**Total TODO/FIXME Items:** 4
**Files Affected:** 3

---

## Summary

| Priority | Count | Total Effort |
|----------|-------|--------------|
| HIGH | 0 | 0 hours |
| MEDIUM | 0 | 0 hours |
| LOW | 4 | 6-30 hours |

---

## TODO/FIXME Items

### Item #1: Delete Bug Feature

- **File:** `src/bridge/bug_cli.py`
- **Line:** 142
- **Type:** TODO
- **Text:** "TODO: Implement delete in tracker"
- **Component:** Bug Tracking CLI
- **Priority:** LOW
- **Impact:** Feature gap - users cannot delete bugs
- **Estimated Effort:** 1-2 hours
- **Complexity:** LOW
- **Dependencies:** BugTracker.delete_bug() method

**Context:**
The bug tracking CLI has list, show, stats, export, and clear commands, but lacks a specific delete command for individual bugs.

**Implementation Plan:**
1. Add `delete_bug(bug_id)` method to BugTracker class
2. Add SQL: `DELETE FROM bugs WHERE id = ?`
3. Add `delete` CLI command with confirmation
4. Verify delete cascades properly if needed

**Acceptance Criteria:**
- User can delete a bug by ID with confirmation
- Deleted bug no longer appears in list/show/stats
- Database integrity maintained

**Recommendation:** Implement before v1.1 release

---

### Item #2: OpenClaw Context Integration

- **File:** `src/bridge/middleware_context_integration.py`
- **Line:** 347
- **Type:** TODO
- **Text:** "TODO: Call OpenClaw with context"
- **Component:** Middleware / OpenClaw Integration
- **Priority:** LOW
- **Impact:** Incomplete OpenClaw context passing
- **Estimated Effort:** 2-4 hours
- **Complexity:** MEDIUM
- **Dependencies:** OpenClaw API specifications

**Context:**
Middleware context integration partially implemented but doesn't complete the OpenClaw context flow.

**Implementation Plan:**
1. Review OpenClaw context API documentation
2. Prepare context payload from middleware
3. Send context to OpenClaw via WebSocket/HTTP
4. Handle context responses
5. Test context propagation through middleware

**Acceptance Criteria:**
- Context properly prepared and sent to OpenClaw
- OpenClaw receives and uses context correctly
- Integration tests validate context flow

**Recommendation:** Implement before v1.0 OR clearly document as v1.1 feature

---

### Item #3: Real Piper TTS Synthesis

- **File:** `src/audio/tts_worker.py`
- **Line:** 268
- **Type:** TODO
- **Text:** "TODO: Implement real Piper TTS synthesis"
- **Component:** TTS Worker / Audio
- **Priority:** LOW
- **Impact:** Using placeholder/mock instead of real TTS
- **Estimated Effort:** 4-8 hours
- **Complexity:** MEDIUM-HIGH
- **Dependencies:** Piper TTS library, audio output

**Context:**
TTS worker currently uses placeholder implementation. Real Piper TTS needs to be integrated for production use.

**Implementation Plan:**
1. Install Piper TTS library (`pip install piper-tts`)
2. Initialize Piper model (download or local)
3. Implement synthesis function
4. Handle audio format conversion
5. Integrate with audio pipeline
6. Add configuration for model selection

**Acceptance Criteria:**
- Piper TTS generates speech from text
- Audio output properly formatted (16kHz, 16-bit)
- Integration with audio pipeline works
- Barge-in interruption of TTS works

**Recommendation:** Implement for v1.0 OR clearly document as current limitation

---

### Item #4: Streaming Synthesis

- **File:** `src/audio/tts_worker.py`
- **Line:** 286
- **Type:** TODO
- **Text:** "TODO: Implement real streaming synthesis"
- **Component:** TTS Worker / Audio
- **Priority:** LOW
- **Impact:** No streaming support - blocking synthesis
- **Estimated Effort:** 4-8 hours
- **Complexity:** MEDIUM-HIGH
- **Dependencies:** Piper streaming API, async architecture

**Context:**
Current implementation uses blocking synthesis. Streaming synthesis would allow TTS to start output immediately rather than waiting for full generation.

**Implementation Plan:**
1. Research Piper streaming API
2. Implement async streaming synthesis
3. Integrate with audio pipeline streaming
4. Handle partial audio buffers
5. Test latency improvements
6. Ensure barge-in still works with streaming

**Acceptance Criteria:**
- TTS streams audio as it generates
- Latency < 50ms from first chunk
- Barge-in interruption works mid-stream
- No audio glitches or gaps

**Recommendation:** Enhancement for v1.1+ - not required for v1.0

---

## Technical Debt Summary

### By Component

| Component | TODOs | Priority | Effort |
|-----------|-------|----------|--------|
| Bug Tracking CLI | 1 | LOW | 1-2 hours |
| Middleware / OpenClaw | 1 | LOW | 2-4 hours |
| TTS Worker | 2 | LOW | 8-16 hours |

### By Complexity

| Complexity | Count | Effort Range |
|------------|-------|--------------|
| LOW | 1 | 1-2 hours |
| MEDIUM | 1 | 2-4 hours |
| MEDIUM-HIGH | 2 | 8-16 hours |

### By Timeline Recommendation

| When | Items | Effort | Reason |
|------|-------|--------|--------|
| **v1.0** | 0 | 0 hrs | Not blocking |
| **v1.0.1** | 1 | 1-2 hrs | Delete bug feature |
| **v1.1** | 1 | 2-4 hrs | OpenClaw context |
| **v1.2** | 2 | 8-16 hrs | Real Piper TTS + streaming |

---

## Risk Assessment

### Low Risk (Recommended Soon)
- Delete bug feature: Simple SQL operation, clear impact

### Medium Risk (Can Defer)
- OpenClaw context: Depends on API, needs testing

### High Complexity (Major Feature Work)
- Piper TTS: New library integration, audio pipeline changes
- Streaming: Async architecture changes, testing heavy

---

## Dependencies

### Piper TTS Items
Both item #3 and #4 depend on:
1. Piper TTS library availability
2. Model file access/bundling
3. Audio pipeline compatibility
4. Testing infrastructure

**Recommendation:** Implement together as a "TTS Enhancement" sprint

### OpenClaw Context
Item #2 depends on:
1. OpenClaw API specification
2. WebSocket message format
3. Integration test infrastructure

**Recommendation:** Coordinate with OpenClaw team for API docs

---

## Conclusion

**Total Technical Debt:** 4 TODO items
**Estimated Total Effort:** 11-22 hours

**Current State:**
- All items are well-documented
- No blockers for v1.0 release
- Clear roadmap for future enhancements

**Recommendation:**
1. Document current limitations in README
2. Plan v1.0.1 for delete bug feature (simple win)
3. Plan v1.1 sprint for OpenClaw context
4. Plan v1.2 sprint for TTS enhancements

---

**Technical Debt: Managed and Roadmapped** ✅