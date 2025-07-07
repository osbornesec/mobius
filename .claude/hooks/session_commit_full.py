#!/usr/bin/env python3
import os
import sys
import subprocess
from datetime import datetime

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def run_command(cmd):
    """Run a shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def get_active_session():
    """Get the active session file path"""
    session_dir = "/home/michael/dev/Mobius/.claude/sessions"
    session_file = f"{session_dir}/.current-session"
    
    if not os.path.exists(session_file):
        print(f"{RED}No active session found at {session_file}{NC}")
        return None
    
    return session_file, session_dir

def check_staged_changes():
    """Check if there are staged changes"""
    stdout, _, code = run_command("git diff --cached --quiet")
    if code == 0:
        print(f"{RED}No changes staged for commit. Aborting.{NC}")
        return False
    print(f"{GREEN}Found staged changes{NC}")
    return True

def read_session_content(session_file):
    """Read and clean session content for commit message"""
    with open(session_file, 'r') as f:
        content = f.read()
    
    # Remove any existing "Note:" system reminders
    import re
    content = re.sub(r'<system-reminder>.*?</system-reminder>', '', content, flags=re.DOTALL)
    
    return content.strip()

def determine_scope(staged_files):
    """Determine commit scope based on staged files"""
    # Analyze staged files to determine scope
    if any('.claude/hooks/' in f for f in staged_files):
        return '[hooks]'
    elif any('.claude/sessions/' in f for f in staged_files):
        return '[sessions]'
    elif any('.claude/commands/' in f for f in staged_files):
        return '[commands]'
    elif any('.claude/' in f for f in staged_files):
        return '[claude]'
    else:
        # Get the most common directory
        dirs = [os.path.dirname(f) for f in staged_files if '/' in f]
        if dirs:
            from collections import Counter
            most_common = Counter(dirs).most_common(1)[0][0]
            return f'[{most_common}]'
        return '[misc]'

def create_commit_with_full_session(session_content, scope):
    """Create a commit with the full session content as the message"""
    # Create a temporary file for the commit message
    import tempfile
    
    # Build the commit message
    summary_line = f"{scope} session work - see full details below"
    
    # Full commit message with session content
    full_message = f"""{summary_line}

{session_content}"""
    
    # Write to temporary file (git can handle large messages better from file)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(full_message)
        temp_file = f.name
    
    try:
        # Use git commit with file to handle large messages
        cmd = f'git commit -F "{temp_file}"'
        stdout, stderr, code = run_command(cmd)
        
        if code == 0:
            print(f"{GREEN}Commit created successfully with full session content!{NC}")
            return True
        else:
            print(f"{RED}Commit failed: {stderr}{NC}")
            return False
    finally:
        # Clean up temp file
        os.unlink(temp_file)

def main():
    # Get active session
    session_info = get_active_session()
    if not session_info:
        sys.exit(1)
    
    session_file, session_dir = session_info
    
    # Check for staged changes
    if not check_staged_changes():
        sys.exit(1)
    
    # Get staged files
    stdout, _, _ = run_command("git diff --cached --name-only")
    staged_files = stdout.split('\n') if stdout else []
    
    # Read session content
    print(f"\n{BLUE}Reading session content...{NC}")
    session_content = read_session_content(session_file)
    
    # Show preview
    print(f"\n{YELLOW}Session content preview (first 500 chars):{NC}")
    print("-" * 60)
    print(session_content[:500])
    if len(session_content) > 500:
        print(f"\n... and {len(session_content) - 500} more characters")
    print("-" * 60)
    
    # Determine scope
    scope = determine_scope(staged_files)
    
    print(f"\n{YELLOW}Commit will include the FULL session content in the message.{NC}")
    print(f"Scope: {scope}")
    print(f"Session size: {len(session_content)} characters")
    
    # Get confirmation
    print(f"\n{GREEN}Create commit with full session content? (y/n):{NC}")
    confirm = input().strip().lower()
    
    if confirm != 'y':
        print(f"{RED}Commit aborted.{NC}")
        sys.exit(1)
    
    # Create the commit
    if create_commit_with_full_session(session_content, scope):
        # Archive the session file
        archive_name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_committed.md"
        archive_path = f"{session_dir}/archive/{archive_name}"
        
        # Create archive directory if needed
        os.makedirs(f"{session_dir}/archive", exist_ok=True)
        
        # Copy current session to archive
        import shutil
        shutil.copy(session_file, archive_path)
        
        # Reset .current-session with fresh content
        new_session_content = f"""# Development Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Session Overview
- **Start Time**: {datetime.now().strftime('%B %d, %Y at %H:%M')}
- **Project**: dev/Mobius
- **Working Directory**: /home/michael/dev/Mobius
- **Previous Session**: Archived as {archive_name}

## Goals
[To be defined - What would you like to work on in this session?]

## Progress
"""
        
        with open(session_file, 'w') as f:
            f.write(new_session_content)
        
        print(f"{GREEN}Session reset complete!{NC}")
        print(f"- Previous session archived as: {BLUE}archive/{archive_name}{NC}")
        print(f"- New session started in: {BLUE}.current-session{NC}")
        print(f"\n{YELLOW}Note: The commit message contains the full session history.{NC}")
        print(f"View it with: git log --format=fuller -1")
    else:
        print(f"{RED}Session not reset due to commit failure.{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()