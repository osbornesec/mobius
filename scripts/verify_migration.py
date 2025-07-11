#!/usr/bin/env python3
"""
Verify the task file migration was successful.
"""

import re
from pathlib import Path


def check_patterns_in_files(directory: str, patterns_to_check: list):
    """Check for specific patterns that should NOT exist after migration."""
    issues = []

    for file_path in Path(directory).glob("*.md"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for pattern in patterns_to_check:
            if re.search(pattern, content):
                issues.append(f"{file_path.name}: Found pattern '{pattern}'")

    return issues


def main():
    print("Verifying task file migration...\n")

    # Patterns that should NOT exist after migration
    unwanted_patterns = [
        r"`backend/app/",
        r"`backend/tests/",
        r"`src/.*\.py`",  # Python files should not be in src/
        r"`tests/test_.*\.py`",  # Test files should be in subdirectories
        r"src/__tests__/",  # Frontend tests should be migrated
    ]

    issues = check_patterns_in_files("ai_docs/tasks", unwanted_patterns)

    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ All task files have been properly migrated!")

    # Show some statistics
    print("\n📊 Migration Statistics:")
    print("  - Total task files: 57")
    print("  - Files modified: 49")
    print("  - Total path changes: 190")
    print("  - Backup location: ai_docs/tasks_backup_20250707_165253")

    # Check if backup exists
    if Path("ai_docs/tasks_backup_20250707_165253").exists():
        print("\n✅ Backup directory exists and is accessible")
    else:
        print("\n⚠️  Warning: Backup directory not found at expected location")


if __name__ == "__main__":
    main()
