#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
import re
from pathlib import Path

def is_env_file_access(tool_name, tool_input):
    """
    Check if any tool is trying to access .env files containing sensitive data.
    """
    if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write', 'Bash']:
        # Check file paths for file-based tools
        if tool_name in ['Read', 'Edit', 'MultiEdit', 'Write']:
            file_path = tool_input.get('file_path', '')
            if '.env' in file_path and not file_path.endswith('.env.sample'):
                return True
        
        # Check bash commands for .env file access
        elif tool_name == 'Bash':
            command = tool_input.get('command', '')
            # Pattern to detect .env file access (but allow .env.sample)
            env_patterns = [
                r'\b\.env\b(?!\.sample)',  # .env but not .env.sample
                r'cat\s+.*\.env\b(?!\.sample)',  # cat .env
                r'echo\s+.*>\s*\.env\b(?!\.sample)',  # echo > .env
                r'touch\s+.*\.env\b(?!\.sample)',  # touch .env
                r'cp\s+.*\.env\b(?!\.sample)',  # cp .env
                r'mv\s+.*\.env\b(?!\.sample)',  # mv .env
            ]
            
            for pattern in env_patterns:
                if re.search(pattern, command):
                    return True
    
    return False

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        
        # Check for .env file access (blocks access to sensitive environment files)
        if is_env_file_access(tool_name, tool_input):
            print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude
        
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            
            # Check for git commit commands
            if re.match(r'^git\s+commit\b', command):
                if '# allow-standard' in command.lower():
                    # Allow commits with the special comment
                    pass
                else:
                    # Check if we should auto-execute the session commit
                    import os
                    auto_commit = os.environ.get('CLAUDE_AUTO_SESSION_COMMIT', 'true').lower() == 'true'
                    
                    if auto_commit:
                        print("""🎯 Git commit intercepted - automatically running session commit workflow...

This will create a commit with your full session history.
To use standard git commit instead, add '# allow-standard' to your command.
To disable auto-execution, set CLAUDE_AUTO_SESSION_COMMIT=false

Running: echo "y" | /home/michael/dev/Mobius/.claude/hooks/session_commit_detailed.sh
""", file=sys.stderr)
                        
                        # Execute the session commit script directly
                        import subprocess
                        result = subprocess.run(
                            'echo "y" | /home/michael/dev/Mobius/.claude/hooks/session_commit_detailed.sh',
                            shell=True,
                            capture_output=False
                        )
                        
                        # Exit with the script's exit code
                        sys.exit(result.returncode)
                    else:
                        print("""🛑 Git commit intercepted!

Instead of using 'git commit' directly, consider using the session-based commit workflow
that includes your complete development session in the commit message.

Available options:
1. Smart commit messages: python3 /home/michael/dev/Mobius/.claude/hooks/session_commit_advanced.py
2. Full session commit: /home/michael/dev/Mobius/.claude/hooks/session_commit_detailed.sh

These scripts will:
- Include your full session history in the commit
- Generate contextual commit messages
- Archive your session and start fresh

To bypass this check, add '# allow-standard' at the end of your command.
Example: git commit -m "your message" # allow-standard
""", file=sys.stderr)
                        sys.exit(2)  # Block the git commit
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'pre_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Gracefully handle JSON decode errors
        sys.exit(0)
    except Exception:
        # Handle any other errors gracefully
        sys.exit(0)

if __name__ == '__main__':
    main()