#!/usr/bin/env python3
import json

# Load the report
with open('migration_report.json', 'r') as f:
    data = json.load(f)

# Find files with many changes
print("Files with the most changes:")
sorted_files = sorted(data['file_changes'].items(), key=lambda x: len(x[1]), reverse=True)

for file, changes in sorted_files[:5]:
    print(f"\nFile: {file}")
    print(f"Number of changes: {len(changes)}")
    print("Sample changes:")
    for change in changes[:3]:
        print(f"  - Line {change['line']}: '{change['original']}' -> '{change['transformed']}'")
        print(f"    Reason: {change['reason']}")
    if len(changes) > 3:
        print(f"  ... and {len(changes) - 3} more changes")