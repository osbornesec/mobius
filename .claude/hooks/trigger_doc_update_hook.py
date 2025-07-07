#!/usr/bin/env python3
import json
import sys
import os

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0) # Exit silently if input is not valid JSON

    tool_name = input_data.get("tool_name", "")
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        sys.exit(0)

    file_path = input_data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Only trigger for code files (e.g., in src/)
    if file_path.startswith(os.path.join(os.getcwd(), "src")) and file_path.endswith((".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".go", ".rs")):
        print(f"Code file '{file_path}' was modified. Consider updating relevant documentation in the 'docs/' directory or running a documentation generator.", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
