#!/usr/bin/env python3
"""
Bug Database Review and Analysis Script

Analyze all bugs in the database and categorize them by:
- Fixed vs Outstanding
- Component
- Severity
- Action required
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load bugs
with open('/tmp/bugs_output.json', 'r') as f:
    bugs = json.load(f)

print(f"╔{'='*68}╗")
print(f"║ BUG DATABASE REVIEW REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ║")
print(f"╚{'='*68}╝")
print()

# Summary statistics
print(f"Total Bugs: {len(bugs)}")
print(f"Critical: {sum(1 for b in bugs if b.get('severity') == 'critical')}")
print(f"High: {sum(1 for b in bugs if b.get('severity') == 'high')}")
print(f"Medium: {sum(1 for b in bugs if b.get('severity') == 'medium')}")
print(f"Low: {sum(1 for b in bugs if b.get('severity') == 'low')}")
print(f"Info: {sum(1 for b in bugs if b.get('severity') == 'info')}")
print()

# Group by component
from collections import defaultdict
by_component = defaultdict(list)
for bug in bugs:
    by_component[bug.get('component', 'unknown')].append(bug)

print("─"*70)
print("Bugs by Component")
print("─"*70)
for comp in sorted(by_component.keys()):
    bugs_in_comp = by_component[comp]
    crits = sum(1 for b in bugs_in_comp if b.get('severity') == 'critical')
    highs = sum(1 for b in bugs_in_comp if b.get('severity') == 'high')
    print(f"\n{comp}: {len(bugs_in_comp)} bugs")
    print(f"  Critical: {crits}, High: {highs}")

print()
print("─"*70)
print("ALL BUGS DETAILED LIST")
print("─"*70)

# List all bugs
for bug in bugs:
    print(f"\n{'='*70}")
    print(f"Bug #{bug['id']}")
    print(f"{'='*70}")
    print(f"Severity:    {bug.get('severity', 'N/A').upper()}")
    print(f"Component:   {bug.get('component', 'N/A')}")
    print(f"Status:      {bug.get('status', 'N/A')}")
    print(f"Date:        {bug.get('timestamp', 'N/A')[:19]}")
    print(f"Title:       {bug.get('title', 'N/A')}")
    print(f"Description: {bug.get('description', 'N/A')[:300]}")
    print(f"Stack Trace: {bug.get('stack_trace', 'N/A')[:300] if bug.get('stack_trace') else 'None'}...")

    # Decode system state
    try:
        system_state = bug.get('system_state', {})
        if isinstance(system_state, str):
            system_state = json.loads(system_state)
        print(f"\nSystem State:")
        print(f"  Python:      {system_state.get('python_version', 'N/A')}")
        print(f"  Platform:    {system_state.get('platform', 'N/A')}")
        print(f"  CPUs:        {system_state.get('cpu_count', 'N/A')}")
        print(f"  Memory (MB): {int(system_state.get('memory_available', 0) / 1024 / 1024) if system_state.get('memory_available') else 'N/A'}")
    except:
        print(f"  System State: Unable to parse")