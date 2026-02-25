#!/usr/bin/env python3
"""Create GitHub issue for bug tracker testing."""

import requests
import json
from pathlib import Path

# Read token
token_path = Path.home() / ".github_token"
token = token_path.read_text().strip()

url = "https://api.github.com/repos/ray1caron/voice-openclaw-bridge-v2/issues"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json"
}

issue_data = {
    "title": "[TASK] Bug Tracker GitHub Integration Testing",
    "body": """**Priority:** P1 | **Component:** bridge | **Sprint:** Sprint 3 (Phase 4)

Create comprehensive test suite for the automated bug tracking system.

## Background
The bug tracker (from Sprint 2) captures errors, system state, and can create GitHub issues automatically. This issue validates that integration works end-to-end.

## Tasks
- [x] Create integration tests for GitHub API communication
- [x] Create test plan document with test cases
- [x] Create manual test script for live testing
- [ ] Run tests and verify all pass
- [ ] Document test results and any issues found

## Files Created
- `tests/integration/test_bug_tracker_github.py` - 15+ integration tests
- `tests/test_plan_bug_tracker.md` - Comprehensive test plan
- `tests/manual_test_bug_tracker.py` - Executable manual test script

## Test Coverage
- Bug capture from exceptions
- System snapshot capture (Python version, platform, memory, audio)
- GitHub issue formatting
- API authentication and error handling
- Rate limiting and backoff
- Auto-creation for critical bugs
- Local storage on API failure

## References
- Related: Issue #17 (OpenClaw Middleware) - bug tracker implemented there
- Source: `src/bridge/bug_tracker.py` (17.5KB)
- CLI: `src/bridge/bug_cli.py` (5.9KB)

## Success Criteria
- All 15+ integration tests pass
- Manual test can create real GitHub issue
- Test plan documented and reviewable""",
    "labels": ["priority::P1", "component::bridge", "sprint-3"]
}

response = requests.post(url, headers=headers, json=issue_data)

if response.status_code == 201:
    data = response.json()
    print(f"Created Issue #{data['number']}: {data['title']}")
    print(f"URL: {data['html_url']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
