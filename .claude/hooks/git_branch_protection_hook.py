#!/usr/bin/env python3
import json
import sys
import subprocess

PROTECTED_BRANCHES = ["main", "master", "develop"]


def get_current_branch():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Exit silently if input is not valid JSON

    tool_name = input_data.get("tool_name", "")
    command = input_data.get("tool_input", {}).get("command", "")

    # Check for git push commands or direct file modifications on protected branches
    is_git_push = tool_name == "Bash" and "git push" in command
    is_file_modification = tool_name in ["Write", "Edit", "MultiEdit"]

    if not (is_git_push or is_file_modification):
        sys.exit(0)

    current_branch = get_current_branch()

    if current_branch and current_branch in PROTECTED_BRANCHES:
        if is_git_push:
            print(
                f"Warning: Attempting to push directly to protected branch '{current_branch}'. Please use a feature branch and a pull request for changes.",
                file=sys.stderr,
            )
            sys.exit(2)  # Block the push operation
        elif is_file_modification:
            print(
                f"Warning: Modifying files directly on protected branch '{current_branch}'. Consider switching to a feature branch.",
                file=sys.stderr,
            )
            # sys.exit(2) # Uncomment to block file modifications on protected branches

    sys.exit(0)


if __name__ == "__main__":
    main()
