#!/usr/bin/env python3
"""Sync all sessions - create missing .last-message files for sessions without tool usage"""
import json
import os
import glob
from datetime import datetime

SESSIONS_DIR = "/home/michael/dev/Mobius/.claude/sessions"
CLAUDE_PROJECTS_DIR = "/home/michael/.claude/projects/-home-michael-dev-Mobius"

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
                
                except:
                    continue
                    
    except:
        pass
    
    return conversation, all_uuids

def main():
    """Process all transcript files and create missing .last-message files"""
    
    # Find all transcript files for this project
    transcript_files = glob.glob(f"{CLAUDE_PROJECTS_DIR}/*.jsonl")
    
    print(f"Found {len(transcript_files)} transcript files")
    
    for transcript_path in transcript_files:
        # Extract session ID from filename
        filename = os.path.basename(transcript_path)
        session_id = filename.replace('.jsonl', '')
        
        last_message_file = f"{SESSIONS_DIR}/.last-message-{session_id}"
        
        # Check if .last-message file exists
        if os.path.exists(last_message_file):
            print(f"✓ {session_id}: .last-message file exists")
            continue
        
        print(f"⚠ {session_id}: Missing .last-message file, creating...")
        
        # Extract all messages and UUIDs
        conversation, all_uuids = extract_all_messages(transcript_path, session_id)
        
        if all_uuids:
            # Create .last-message file with all UUIDs
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            with open(last_message_file, 'w') as f:
                for uuid in all_uuids:
                    f.write(uuid + '\n')
            
            print(f"  Created .last-message file with {len(all_uuids)} message UUIDs")
            print(f"  Session has {len(conversation)} conversation messages")
        else:
            print(f"  No messages found in session")

if __name__ == '__main__':
    main()