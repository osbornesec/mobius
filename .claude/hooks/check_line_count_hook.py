#!/usr/bin/env python3
import json
import sys
import os

MAX_LINES = 300


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Exit silently if input is not valid JSON

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    file_path = input_data.get("tool_input", {}).get("file_path", "")
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        sys.exit(0)

    # Only check code files (adjust extensions as needed)
    if not file_path.endswith(
        (
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".py",
            ".java",
            ".go",
            ".rs",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
        ),
    ):
        sys.exit(0)

    try:
        with open(file_path, encoding="utf-8") as f:
            line_count = sum(1 for line in f)
        if line_count > MAX_LINES:
            print(
                f"Suggestion: File '{file_path}' has {line_count} lines, which exceeds the recommended {MAX_LINES} lines. Consider refactoring this file to improve readability and maintainability.",
                file=sys.stderr,
            )
    except (IOError, OSError, UnicodeDecodeError) as e:
        # Log error but don't block operation
        print(f"Error checking line count for {file_path}: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
