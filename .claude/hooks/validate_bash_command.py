#!/usr/bin/env python3
import json
import re
import sys

# Define validation rules as (regex pattern, message, is_dangerous) tuples
VALIDATION_RULES = [
    # Performance suggestions
    (r"\bgrep\b(?!.*\|)", "Suggestion: Use 'rg' (ripgrep) instead of 'grep' for better performance and features.", False),
    (r"\bfind\s+\S+\s+-name\b", "Suggestion: Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance.", False),
    
    # Security warnings
    (r"\brm\s+-rf\s+/(?:\s|$)", "DANGER: Attempting to remove root directory! Blocking command.", True),
    (r"\brm\s+-rf\s+~(?:/|$|\s)", "DANGER: Attempting to remove home directory! Blocking command.", True),
    (r"\bdd\s+.*of=/dev/[sh]d[a-z](?:\d|$)", "DANGER: Direct disk write operation detected! Blocking command.", True),
    (r">\s*/dev/[sh]d[a-z]", "DANGER: Attempting to write directly to disk device! Blocking command.", True),
    (r"\bsudo\s+chmod\s+-R\s+777\b", "DANGER: Recursive chmod 777 is extremely insecure! Blocking command.", True),

    # Insecure practices
    (r"\bchmod\s+777\b", "Security Warning: chmod 777 gives full permissions to everyone. This is likely insecure.", False),
]

def validate_command(command: str) -> tuple[list[str], bool]:
    """
    Validate a command and return (issues, should_block).
    """
    issues = []
    should_block = False
    
    for pattern, message, is_dangerous in VALIDATION_RULES:
        if re.search(pattern, command, re.IGNORECASE):
            issues.append(message)
            if is_dangerous:
                should_block = True
    
    return issues, should_block

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0) # Exit silently if input is not valid JSON
    
    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)
    
    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    issues, should_block = validate_command(command)

    if issues:
        for message in issues:
            print(f"• {message}", file=sys.stderr)
        
        if should_block:
            # Exit code 2 blocks the tool call and shows stderr to Claude
            sys.exit(2)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
