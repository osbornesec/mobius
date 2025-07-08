#!/usr/bin/env python3
"""Sync all sessions - create missing .last-message files for sessions without tool usage"""
import json
import os
import glob
from datetime import datetime
from pathlib import Path

# Dynamically determine paths based on script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up two levels: hooks -> .claude -> project root
SESSIONS_DIR = PROJECT_ROOT / ".claude" / "sessions"

# Dynamically construct Claude projects directory path
# Convert project root path to Claude projects format (replace slashes with dashes, remove leading slash)
project_path_str = str(PROJECT_ROOT).replace(os.sep, '-')
if project_path_str.startswith('-'):
    project_path_str = project_path_str[1:]
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects" / project_path_str

def extract_all_messages(transcript_path, session_id):
    """Extract all conversation messages from a transcript file"""
    
    conversation = []
    all_uuids = []
    
    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    if entry.get('sessionId') != session_id:
                        continue
                    
                    entry_uuid = entry.get('uuid')
                    entry_type = entry.get('type', 'unknown')
                    
                    # Only process user/assistant messages
                    if entry_type in ['user', 'assistant']:
                        message = entry.get('message', {})
                        role = message.get('role', 'unknown')
                        content = message.get('content', [])
                        
                        # Track UUID
                        if entry_uuid:
                            all_uuids.append(entry_uuid)
                        
                        # Extract text content
                        text_parts = []
                        if isinstance(content, str):
                            if content.strip():
                                text_parts.append(content)
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if text.strip():
                                        text_parts.append(text)
                        
                        if text_parts:
                            full_text = ' '.join(text_parts).strip()
                            if full_text:
                                conversation.append((role, full_text))
                
                except json.JSONDecodeError:
                    continue
                    
    except (IOError, OSError):
        pass
    
    return conversation, all_uuids

def main():
    """Process all transcript files and create missing .last-message files"""
    
    # Find all transcript files for this project
    transcript_files = list(CLAUDE_PROJECTS_DIR.glob("*.jsonl"))
    
    print(f"Found {len(transcript_files)} transcript files")
    
    for transcript_path in transcript_files:
        # Extract session ID from filename
        session_id = transcript_path.stem  # Get filename without extension
        
        last_message_file = SESSIONS_DIR / f".last-message-{session_id}"
        
        # Check if .last-message file exists
        if last_message_file.exists():
            print(f"✓ {session_id}: .last-message file exists")
            continue
        
        print(f"⚠ {session_id}: Missing .last-message file, creating...")
        
        # Extract all messages and UUIDs
        conversation, all_uuids = extract_all_messages(str(transcript_path), session_id)
        
        if all_uuids:
            # Create .last-message file with all UUIDs
            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            with open(str(last_message_file), 'w') as f:
                for uuid in all_uuids:
                    f.write(uuid + '\n')
            
            print(f"  Created .last-message file with {len(all_uuids)} message UUIDs")
            print(f"  Session has {len(conversation)} conversation messages")
        else:
            print(f"  No messages found in session")

if __name__ == '__main__':
    main()