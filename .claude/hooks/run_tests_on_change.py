#!/usr/bin/env python3
import json
import sys
import subprocess
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

    # Only run tests if a file in the src/ directory was modified
    if not file_path.startswith(os.path.join(os.getcwd(), "src")):
        sys.exit(0)

    # Determine the test command. Assuming npm test for a React project.
    # In a more complex scenario, you might parse package.json or pyproject.toml
    # to find the actual test command.
    test_command = ["npm", "test", "--", "--watchAll=false"]

    try:
        # Run tests in the background and capture output
        # Using stderr for output so it doesn't interfere with tool output
        process = subprocess.run(test_command, capture_output=True, text=True, check=False)
        
        if process.returncode != 0:
            print(f"Tests failed for {file_path}:\n{process.stdout}\n{process.stderr}", file=sys.stderr)
        else:
            print(f"Tests passed for {file_path}.", file=sys.stderr)

    except FileNotFoundError:
        print(f"Error: Test command 'npm' not found. Please ensure Node.js and npm are installed.", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred while running tests: {e}", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
