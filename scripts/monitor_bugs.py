#!/usr/bin/env python3
"""
Bug Database Monitor

Monitors the bug tracking database for new bugs being created.
Run periodically to check for new bug reports.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bridge.bug_tracker import BugTracker, BugStatus

def check_for_new_bugs():
    """Check for new bugs in the database."""
    tracker = BugTracker.get_instance()
    
    # Get all bugs
    all_bugs = tracker.list_bugs()
    
    # Filter for NEW bugs (not FIXED, CLOSED)
    new_bugs = [bug for bug in all_bugs if bug.status == BugStatus.NEW]
    
    # Filter for bugs created in last hour (recent)
    now = datetime.now()
    recent_bugs = [
        bug for bug in new_bugs
        if (now - bug.created_at).total_seconds() < 3600
    ]
    
    print("="*70)
    print(f"BUG DATABASE MONITOR - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print(f"\n📊 Database Statistics:")
    print(f"   Total bugs: {len(all_bugs)}")
    print(f"   New (unread): {len(new_bugs)}")
    print(f"   Recent (last hour): {len(recent_bugs)}")
    
    if recent_bugs:
        print(f"\n🚨 NEW BUGS DETECTED ({len(recent_bugs)}):")
        for bug in recent_bugs:
            age_mins = int((now - bug.created_at).total_seconds() / 60)
            print(f"\n   🔴 Bug #{bug.id}: {bug.title}")
            print(f"      Severity: {bug.severity.value}")
            print(f"      Component: {bug.component}")
            print(f"      Created: {bug.created_at.strftime('%H:%M:%S')} ({age_mins} mins ago)")
            print(f"      Description: {bug.description[:100]}...")
    else:
        print(f"\n✅ No new bugs in the last hour")
    
    print("\n" + "="*70)
    
    return recent_bugs

def main():
    """Main monitoring loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor bug database for new bugs")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")
    
    args = parser.parse_args()
    
    if args.once:
        bugs = check_for_new_bugs()
        sys.exit(1 if bugs else 0)
    else:
        print(f"🔍 Monitoring bug database every {args.interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        try:
            last_count = 0
            while True:
                bugs = check_for_new_bugs()
                
                if len(bugs) > last_count:
                    print(f"🚨 ALERT: {len(bugs) - last_count} new bugs since last check!")
                    last_count = len(bugs)
                
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n⏹ Monitoring stopped")

if __name__ == "__main__":
    main()