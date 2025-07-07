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

    # Check for common dependency manifest files
    manifest_files = [
        "package.json", # Node.js/npm
        "requirements.txt", # Python/pip
        "Cargo.toml", # Rust/Cargo
        "pom.xml", # Java/Maven
        "build.gradle", # Java/Gradle
        "go.mod", # Go modules
    ]

    if os.path.basename(file_path) in manifest_files:
        print(f"Dependency manifest file '{os.path.basename(file_path)}' was modified. Consider running a dependency update/audit (e.g., npm install, pip install, cargo update).", file=sys.stderr)

    sys.exit(0)

if __name__ == "__main__":
    main()
