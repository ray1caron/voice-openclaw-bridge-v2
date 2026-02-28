#!/bin/bash
# Delete redundant .md files

cd /home/hal/.openclaw/workspace/voice-bridge-v2

echo "=== Deleting redundant .md files ==="

# Historical/superseded files
echo "Deleting historical status files..."

# Project status files (superseded by STATUS.md)
rm -f PROJECT.md PROJECT_STATUS_2026-02-26.md
echo "  Deleted: PROJECT.md, PROJECT_STATUS_2026-02-26.md"

# Design review (old)
rm -f SYSTEM_DESIGN_REVIEW_2026-02-26.md
echo "  Deleted: SYSTEM_DESIGN_REVIEW_2026-02-26.md"

# Quick docs (superseded)
rm -f QUICKSTART.md QUICK_STATUS.md
echo "  Deleted: QUICKSTART.md, QUICK_STATUS.md"

# Old implementation/architecture plans
rm -f voice-assistant-plan-v2.md VOICE_BRIDGE_V2_IMPLEMENTATION_PLAN_V2.md
echo "  Deleted: voice-assistant-plan-v2.md, VOICE_BRIDGE_V2_IMPLEMENTATION_PLAN_V2.md"

# GitHub checklist (one-time use)
rm -f GITHUB_VERIFICATION_CHECKLIST.md
echo "  Deleted: GITHUB_VERIFICATION_CHECKLIST.md"

# Old requirements (superseded by TEST_ENVIRONMENT.md)
rm -f PYTHON_312_TESTING_REQUIREMENTS.md
echo "  Deleted: PYTHON_312_TESTING_REQUIREMENTS.md"

# Test directory
rm -f tests/test_plan_bug_tracker.md tests/TEST_PLAN.md
echo "  Deleted: tests/test_plan_bug_tracker.md, tests/TEST_PLAN.md"

rm -f tests/integration/BUG_TRACKER_TEST_RESULTS.md
echo "  Deleted: tests/integration/BUG_TRACKER_TEST_RESULTS.md"

echo ""
echo "=== Cleanup complete ==="
echo ""
echo "Keeping essential documentation:"
echo "  README.md, INSTALL.md, USER_GUIDE.md"
echo "  IMPLEMENTATION_PLAN.md, COMMERCIAL_READINESS_ASSESSMENT.md, STATUS.md"
echo "  SYSTEM_TEST_PLAN.md, TEST_ENVIRONMENT.md, BUG_TRACKER.md"
echo "  MVP.md"
echo ""
echo "Count remaining .md files:"
ls -1 *.md tests/**/*.md 2>/dev/null | wc -l