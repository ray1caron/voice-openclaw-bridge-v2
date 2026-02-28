#!/usr/bin/env python3
"""
Analyze outstanding bugs that weren't marked as fixed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load bugs
with open('/tmp/bugs_output.json', 'r') as f:
    all_bugs = json.load(f)

# Test bugs that were marked as FIXED
test_bug_ids = {2, 4, 7, 9, 11, 13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 28, 40, 42, 43}

# Get outstanding bugs (not in test_bug_ids)
outstanding_bugs = [b for b in all_bugs if b['id'] not in test_bug_ids]

print("="*70)
print(f"OUTSTANDING BUGS ANALYSIS")
print("="*70)
print(f"\nTotal outstanding bugs: {len(outstanding_bugs)}")
print(f"Test bugs marked as FIXED: {len(test_bug_ids)}")
print(f"Total bugs in database: {len(all_bugs)}")
print()

# Group by severity
from collections import defaultdict
outstanding_by_severity = defaultdict(list)
for bug in outstanding_bugs:
    outstanding_by_severity[bug.get('severity', 'unknown')].append(bug)

print("By Severity:")
for sev in ['critical', 'high', 'medium', 'low', 'info']:
    if sev in outstanding_by_severity:
        bugs = outstanding_by_severity[sev]
        print(f"  {sev.upper()}: {len(bugs)}")

print()
print("="*70)
print("DETAILED ANALYSIS")
print("="*70)

# Analyze each outstanding bug
for bug in sorted(outstanding_bugs, key=lambda b: b['id']):
    print(f"\n{'='*70}")
    print(f"Bug #{bug['id']}")
    print(f"{'='*70}")
    print(f"Severity:    {bug.get('severity', 'N/A').upper()}")
    print(f"Component:   {bug.get('component', 'N/A')}")
    print(f"Status:      {bug.get('status', 'N/A')}")
    print(f"Date:        {bug.get('timestamp', 'N/A')[:19]}")
    print(f"Title:       {bug.get('title', 'N/A')}")
    print(f"Description: {bug.get('description', 'N/A')}")

    print(f"\nStack Trace (first 500 chars):")
    stack = bug.get('stack_trace', 'N/A')
    if stack:
        print(f"  {stack[:500]}")
    else:
        print(f"  None")

    # Try to get more details from the full trace
    if stack and len(stack) > 500:
        print(f"  ... ({len(stack)} total characters)")

    # Evaluate the bug
    print(f"\nEVALUATION:")
    is_test_bug = 'test' in stack.lower() or 'test' in bug.get('title', '').lower() or 'test' in bug.get('component', '').lower()
    is_simulated = 'simulated' in bug.get('description', '').lower() or 'simulated' in bug.get('title', '').lower()

    if is_test_bug or is_simulated:
        print(f"  → This appears to be a TEST BUG - should be marked FIXED")
    else:
        print(f"  → REAL BUG requiring investigation")

        # Suggested actions
        if 'audio' in bug.get('component', '').lower():
            print(f"  → Action: Review audio pipeline implementation")
        if 'websocket' in bug.get('component', '').lower():
            print(f"  → Action: Check WebSocket connection handling")
        if 'config' in bug.get('component', '').lower():
            print(f"  → Action: Verify configuration validation")

print()
print("="*70)
print("SUMMARY")
print("="*70)
print(f"Outstanding bugs to review: {len(outstanding_bugs)}")
print(f"Test bugs already marked: {len(test_bug_ids)}")
print()
print("Next steps:")
print("1. Review remaining test bugs in outstanding list")
print("2. Investigate real bugs requiring action")
print("3. Create remediation plan")