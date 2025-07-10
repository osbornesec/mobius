#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
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

def format_with_prettier(tool_name, tool_input):
    """
    Format files with Prettier when they're being edited or written.
    Supports YAML, JSON, JavaScript, TypeScript, CSS, and more.
    """
    if tool_name in ['Edit', 'MultiEdit', 'Write']:
        file_path = tool_input.get('file_path', '')
        file_path_obj = Path(file_path)
        
        # Check if it's a file type that Prettier supports
        prettier_extensions = {
            '.yml', '.yaml', '.json', '.js', '.jsx', '.ts', '.tsx', 
            '.css', '.scss', '.less', '.html', '.md', '.mdx'
        }
        
        if any(file_path.endswith(ext) for ext in prettier_extensions):
            # For Write operations, spawn a background process to format after write
            if tool_name == 'Write':
                print(f"📝 Will format {file_path} with Prettier after write completes", file=sys.stderr)
                
                subprocess.Popen(
                    ['/bin/bash', '-c', f'sleep 1 && npx prettier --write {shlex.quote(str(file_path))} 2>/dev/null || true'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                return
            
            # For Edit/MultiEdit, format the existing file before the edit
            if tool_name in ['Edit', 'MultiEdit'] and file_path_obj.exists():
                try:
                    # Try to find prettier executable
                    prettier_paths = [
                        Path.cwd() / 'node_modules' / '.bin' / 'prettier',
                        Path.home() / '.npm' / 'bin' / 'prettier',
                    ]
                    
                    prettier_cmd = None
                    for prettier_path in prettier_paths:
                        if prettier_path.exists():
                            prettier_cmd = str(prettier_path)
                            break
                    
                    # If not found in common locations, try npx
                    if not prettier_cmd:
                        prettier_cmd = 'npx'
                        prettier_args = ['prettier', '--write', str(file_path_obj)]
                    else:
                        prettier_args = [prettier_cmd, '--write', str(file_path_obj)]
                    
                    # Set up environment
                    env = os.environ.copy()
                    env['LC_ALL'] = 'C'
                    
                    # Run prettier to format the file
                    result = subprocess.run(
                        prettier_args,
                        capture_output=True,
                        text=True,
                        cwd=Path.cwd(),
                        env=env
                    )
                    
                    if result.returncode == 0:
                        print(f"✨ Formatted {file_path} with Prettier", file=sys.stderr)
                    elif 'prettier' not in result.stderr.lower() or 'not found' not in result.stderr.lower():
                        # Only show errors if it's not a "prettier not found" error
                        print(f"⚠️  Prettier formatting failed for {file_path}:", file=sys.stderr)
                        if result.stderr:
                            print(result.stderr, file=sys.stderr)
                except FileNotFoundError:
                    # npx or prettier not installed, skip silently
                    pass
                except subprocess.CalledProcessError as e:
                    # Log subprocess errors with command details
                    sys.stderr.write(f"⚠️  Prettier formatting failed for {file_path}: {type(e).__name__}\n")
                    if e.stderr:
                        sys.stderr.write(f"   Error output: {e.stderr}\n")
                except OSError as e:
                    # Log OS-related errors (permissions, etc.)
                    sys.stderr.write(f"⚠️  OS error while formatting {file_path}: {type(e).__name__}: {str(e)}\n")
                except Exception as e:
                    # Log unexpected errors for debugging
                    sys.stderr.write(f"⚠️  Unexpected error while formatting {file_path}: {type(e).__name__}: {str(e)}\n")
                    # Include traceback for unexpected errors to aid debugging
                    import traceback
                    sys.stderr.write(f"   Traceback: {traceback.format_exc()}\n")

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
        
        # Format files with Prettier
        format_with_prettier(tool_name, tool_input)
        
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            
            # Check for git commit commands
            if re.match(r'^git\s+commit\b', command):
                if '# allow-standard' in command.lower():
                    # Allow commits with the special comment
                    pass
                else:
                    # Check if we should auto-execute the session commit
                    auto_commit = os.environ.get('CLAUDE_AUTO_SESSION_COMMIT', 'true').lower() == 'true'
                    
                    # Get the hooks directory path relative to current working directory
                    hooks_dir = Path.cwd() / '.claude' / 'hooks'
                    session_commit_script = hooks_dir / 'session_commit_detailed.sh'
                    session_commit_advanced_script = hooks_dir / 'session_commit_advanced.py'
                    
                    if auto_commit:
                        print(f"""🎯 Git commit intercepted - automatically running session commit workflow...

This will create a commit with your full session history.
To use standard git commit instead, add '# allow-standard' to your command.
To disable auto-execution, set CLAUDE_AUTO_SESSION_COMMIT=false

Running: echo "y" | {session_commit_script}
""", file=sys.stderr)
                        
                        # Execute the session commit script directly
                        # Wait a moment to ensure session file is fully written
                        # Polling for session lock file to be released
                        sessions_dir = Path.cwd() / '.claude' / 'sessions'
                        lock_file = sessions_dir / '.session.lock'
                        timeout = 35  # seconds
                        start_time = time.time()
                        
                        if lock_file.exists():
                            print("⏳ Waiting for session file to be ready...", file=sys.stderr)
                            while lock_file.exists():
                                if time.time() - start_time > timeout:
                                    print("⌛️ Timeout waiting for session lock file. Proceeding anyway.", file=sys.stderr)
                                    break
                                time.sleep(0.5)
                            print("✅ Session file is ready.", file=sys.stderr)
                        
                        result = subprocess.run(
                            f'echo "y" | {session_commit_script}',
                            shell=True,
                            capture_output=False
                        )
                        
                        # Exit with the script's exit code
                        sys.exit(result.returncode)
                    else:
                        print(f"""🛑 Git commit intercepted!

Instead of using 'git commit' directly, consider using the session-based commit workflow
that includes your complete development session in the commit message.

Available options:
1. Smart commit messages: python3 {session_commit_advanced_script}
2. Full session commit: {session_commit_script}

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