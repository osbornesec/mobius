#!/usr/bin/env python3
import os
import sys
import re
import subprocess
from datetime import datetime
from collections import Counter, defaultdict

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
    current_session_file = f"{session_dir}/.current-session"
    
    if not os.path.exists(current_session_file):
        print(f"{RED}No active session found{NC}")
        return None
    
    with open(current_session_file, 'r') as f:
        session_name = f.read().strip()
    
    session_file = f"{session_dir}/{session_name}"
    if not os.path.exists(session_file):
        print(f"{RED}Session file not found: {session_file}{NC}")
        return None
    
    return session_file, session_name, session_dir

def check_staged_changes():
    """Check if there are staged changes"""
    stdout, _, code = run_command("git diff --cached --quiet")
    if code == 0:
        print(f"{RED}No changes staged for commit. Aborting.{NC}")
        return False
    print(f"{GREEN}Found staged changes{NC}")
    return True

def analyze_session(session_file):
    """Analyze session file to extract meaningful information"""
    with open(session_file, 'r') as f:
        content = f.read()
    
    # Extract different types of operations
    operations = {
        'reads': re.findall(r'\[.*?\] File Read\n\n\*\*File:\*\* `(.*?)`', content),
        'writes': re.findall(r'\[.*?\] File Write\n\n\*\*File:\*\* `(.*?)`', content),
        'edits': re.findall(r'\[.*?\] File Edit\n\n\*\*File:\*\* `(.*?)`', content),
        'commands': re.findall(r'\[.*?\] Bash Command\n\n\*\*Description:\*\* (.*?)\n', content),
        'todos': len(re.findall(r'\[.*?\] Todo Update', content))
    }
    
    # Count operations
    stats = {
        'File Reads': len(operations['reads']),
        'File Writes': len(operations['writes']),
        'File Edits': len(operations['edits']),
        'Bash Commands': len(operations['commands']),
        'Todo Updates': operations['todos']
    }
    
    # Get unique files modified
    all_files = operations['writes'] + operations['edits']
    unique_files = list(set(all_files))
    
    # Analyze file types and directories
    file_analysis = defaultdict(list)
    for file in unique_files:
        if '/.claude/hooks/' in file:
            file_analysis['hooks'].append(file)
        elif '/.claude/sessions/' in file:
            file_analysis['sessions'].append(file)
        elif '/.claude/commands/' in file:
            file_analysis['commands'].append(file)
        elif file.endswith('.sh'):
            file_analysis['scripts'].append(file)
        elif file.endswith('.py'):
            file_analysis['python'].append(file)
        elif file.endswith('.md'):
            file_analysis['docs'].append(file)
        else:
            file_analysis['other'].append(file)
    
    # Extract goals
    goals_match = re.search(r'## Goals\n(.*?)(?=\n##)', content, re.DOTALL)
    goals = goals_match.group(1).strip() if goals_match else ""
    
    return stats, unique_files, file_analysis, operations, goals

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
    elif any(f.endswith('.sh') for f in staged_files):
        return '[scripts]'
    elif any(f.endswith('.py') for f in staged_files):
        return '[python]'
    elif any(f.endswith('.md') for f in staged_files):
        return '[docs]'
    else:
        return '[misc]'

def generate_commit_messages(stats, file_analysis, operations, goals, scope):
    """Generate intelligent commit message suggestions"""
    messages = []
    
    # Analyze the primary activity
    primary_activity = None
    if file_analysis['hooks']:
        if any('log_tool_usage.sh' in f for f in file_analysis['hooks']):
            messages.append(f"{scope} fix tool usage logging with proper JSON parsing and formatting")
            messages.append(f"{scope} implement session-based tool activity tracking")
        if any('session_commit' in f for f in file_analysis['hooks']):
            messages.append(f"{scope} add automated commit message generation from session data")
            messages.append(f"{scope} implement session reset workflow after commits")
    
    # Look for specific patterns in commands
    if operations['commands']:
        cmd_summary = ' '.join(operations['commands']).lower()
        if 'test' in cmd_summary:
            messages.append(f"{scope} test and fix hook functionality")
        if 'debug' in cmd_summary:
            messages.append(f"{scope} debug and resolve hook execution issues")
    
    # Check for configuration changes
    if stats['File Edits'] > 0:
        messages.append(f"{scope} update configuration and fix implementation issues")
    
    # If we have specific goals, use them
    if goals and goals != "[To be defined - What would you like to work on in this session?]":
        goal_lines = goals.split('\n')
        for line in goal_lines[:3]:  # First 3 goal lines
            if line.strip() and not line.startswith('['):
                clean_goal = line.strip('- ').lower()
                messages.append(f"{scope} {clean_goal}")
    
    # Add generic but contextual messages
    if file_analysis['hooks'] and file_analysis['sessions']:
        messages.append(f"{scope} enhance session tracking with automated workflows")
    
    # Ensure we have at least 5 messages
    while len(messages) < 5:
        if stats['File Writes'] > 0:
            messages.append(f"{scope} add new functionality for session management")
        elif stats['File Edits'] > 0:
            messages.append(f"{scope} improve existing implementation")
        else:
            messages.append(f"{scope} update project configuration")
    
    return messages[:5]  # Return only first 5

def main():
    # Get active session
    session_info = get_active_session()
    if not session_info:
        sys.exit(1)
    
    session_file, session_name, session_dir = session_info
    
    # Check for staged changes
    if not check_staged_changes():
        sys.exit(1)
    
    # Get staged files
    stdout, _, _ = run_command("git diff --cached --name-only")
    staged_files = stdout.split('\n') if stdout else []
    
    # Analyze session
    print(f"\n{BLUE}Analyzing session activity...{NC}")
    stats, unique_files, file_analysis, operations, goals = analyze_session(session_file)
    
    # Determine scope
    scope = determine_scope(staged_files)
    
    # Display session summary
    print(f"\n{YELLOW}Session Summary:{NC}")
    for key, value in stats.items():
        print(f"- {key}: {value}")
    
    if unique_files:
        print(f"\n{YELLOW}Modified Files:{NC}")
        for file in unique_files[:10]:  # Show first 10
            print(f"  - {os.path.basename(file)}")
        if len(unique_files) > 10:
            print(f"  ... and {len(unique_files) - 10} more")
    
    # Generate commit messages
    messages = generate_commit_messages(stats, file_analysis, operations, goals, scope)
    
    print(f"\n{YELLOW}Suggested commit messages:{NC}")
    for i, msg in enumerate(messages, 1):
        print(f"{YELLOW}{i}. {msg}{NC}")
    
    # Get user choice
    print(f"\n{GREEN}Choose a message number (1-5) or type your own:{NC}")
    choice = input().strip()
    
    # Handle the choice
    if choice.isdigit() and 1 <= int(choice) <= 5:
        commit_msg = messages[int(choice) - 1]
    elif choice:
        # User typed their own message
        if not choice.startswith('['):
            commit_msg = f"{scope} {choice}"
        else:
            commit_msg = choice
    else:
        print(f"{RED}No message selected. Aborting.{NC}")
        sys.exit(1)
    
    print(f"\n{GREEN}Selected commit message:{NC} {commit_msg}")
    print(f"{YELLOW}Proceed with commit? (y/n):{NC}")
    confirm = input().strip().lower()
    
    if confirm != 'y':
        print(f"{RED}Commit aborted.{NC}")
        sys.exit(1)
    
    # Create the commit
    _, stderr, code = run_command(f'git commit -m "{commit_msg}"')
    
    if code == 0:
        print(f"{GREEN}Commit created successfully!{NC}")
        
        # Archive the session file
        archive_name = session_name.replace('.md', '-committed.md')
        os.rename(session_file, f"{session_dir}/{archive_name}")
        
        # Create a new session
        new_session_content = f"""# Development Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Session Overview
- **Start Time**: {datetime.now().strftime('%B %d, %Y at %H:%M')}
- **Project**: dev/Mobius
- **Working Directory**: /home/michael/dev/Mobius
- **Previous Session**: Committed as '{commit_msg}'

## Goals
[To be defined - What would you like to work on in this session?]

## Progress
"""
        
        with open(session_file, 'w') as f:
            f.write(new_session_content)
        
        print(f"{GREEN}Session reset complete!{NC}")
        print(f"- Previous session archived as: {BLUE}{archive_name}{NC}")
        print(f"- New session started: {BLUE}{session_name}{NC}")
    else:
        print(f"{RED}Commit failed: {stderr}{NC}")
        print(f"{RED}Session not reset.{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()