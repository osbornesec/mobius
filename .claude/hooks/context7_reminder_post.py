#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys

# Read the input from stdin
try:
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Different messages for different tools
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if file_path.endswith(
            (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".go", ".rs")
        ):
            print("use context7", file=sys.stderr)
            sys.exit(2)

    elif tool_name == "TodoWrite":
        print(
            "use subagents to complete each todo. Also, use context7 for context on the libraries, languages, and frameworks you are using",
            file=sys.stderr,
        )
        sys.exit(2)

    elif tool_name == "TodoRead":
        print(
            "use subagents to complete each todo. Also, use context7 for context on the libraries, languages, and frameworks you are using",
            file=sys.stderr,
        )
        sys.exit(2)

    elif tool_name in ["Glob", "Grep"]:
        print("use context7", file=sys.stderr)
        sys.exit(2)

except Exception:
    pass

# For all other cases, exit normally
sys.exit(0)
