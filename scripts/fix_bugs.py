#!/usr/bin/env python3
"""
Mark specific bugs as FIXED.

Usage: python3 fix_bugs.py <bug_ids...>
Example: python3 fix_bugs.py 1 2 3
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bridge.bug_tracker import BugTracker, BugStatus

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_bugs.py <bug_id1> <bug_id2> ...")
        print("Example: python3 fix_bugs.py 1 2 3")
        sys.exit(1)

    bug_ids = [int(arg) for arg in sys.argv[1:]]
    tracker = BugTracker.get_instance()

    print("Marking bugs as FIXED:")
    print("="*50)

    for bug_id in bug_ids:
        bug = tracker.get_bug(bug_id)
        if bug:
            old_status = bug.get('status')
            # Update status
            tracker.update_bug_status(bug_id, BugStatus.FIXED)
            print(f"✓ Bug #{bug_id}: {old_status} → FIXED")
            print(f"  Title: {bug.get('title')}")
        else:
            print(f"✗ Bug #{bug_id}: NOT FOUND")

    print("\nDone. Use 'bug_cli list --status fixed' to verify.")

if __name__ == "__main__":
    main()