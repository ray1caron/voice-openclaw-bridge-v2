#!/bin/bash
# Git commands to push Issue #20 changes to GitHub
# Run this script from the voice-bridge-v2 directory

cd "$(dirname "$0")"

echo "=== Adding files to staging ==="
git add tests/unit/test_websocket_client.py
git add tests/integration/test_session_integration.py
echo "Files staged:"
git status --short

echo ""
echo "=== Committing changes ==="
git commit -m "feat(#20): WebSocket Session Lifecycle Integration

Phase 1 of Sprint 3 integration complete:
- Add session creation on WebSocket connect (websocket_client.py:260-275)
- Implement message persistence with metadata (websocket_client.py:500-555)
- Add session closure on disconnect (websocket_client.py:337-351)
- Include enable_persistence feature flag (config.py:93-99)
- Add 6 unit tests in TestWebSocketSessionPersistence class
- Add 14 integration tests in test_session_integration.py
- All acceptance criteria verified

Closes #20

Test Coverage:
- test_session_created_on_connect
- test_message_persisted_on_send
- test_session_closed_on_disconnect
- test_persistence_feature_flag_enabled/disabled
- test_message_persisted_with_metadata"

echo ""
echo "=== Pushing to GitHub ==="
git push origin main

echo ""
echo "=== Done ==="
echo "Check https://github.com/ray1caron/voice-openclaw-bridge-v2 for updates"
