#!/usr/bin/env python3
"""Extract conversation data incrementally, showing only new messages since last run"""
import json
import sys
import os
from datetime import datetime

def main():
    if len(sys.argv) < 3:
        sys.exit(0)
    
    transcript_path = sys.argv[1]
    session_id = sys.argv[2]
    
    # Check for mode flags
    simple_mode = "--simple" in sys.argv
    debug_mode = "--debug" in sys.argv
    
    # Get last message file path
    last_message_file = None
    for i, arg in enumerate(sys.argv):
        if arg == "--last-file" and i + 1 < len(sys.argv):
            last_message_file = sys.argv[i + 1]
            break
    
    if debug_mode:
        print(f"🔍 Analyzing conversation for session: {session_id}")
        print("=" * 80)
    
    # Read the last processed message UUID
    last_uuid = None
    if last_message_file and os.path.exists(last_message_file):
        try:
            with open(last_message_file, 'r') as f:
                last_uuid = f.read().strip()
        except:
            pass
    
    conversation = []
    found_last_message = False if last_uuid else True
    latest_uuid = None
    entry_count = 0
    
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
                    
                    # If we haven't found the last message yet, skip
                    if not found_last_message:
                        if entry_uuid == last_uuid:
                            found_last_message = True
                        continue
                    
                    # Skip the last message itself (we want messages AFTER it)
                    if entry_uuid == last_uuid:
                        continue
                    
                    entry_count += 1
                    
                    # Debug mode output
                    if debug_mode and not simple_mode:
                        timestamp = datetime.fromtimestamp(entry.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                        is_meta = entry.get('isMeta', False)
                        print(f"\n[{entry_count}] {timestamp} | Type: {entry_type} | Meta: {is_meta}")
                        print(f"🔍 Entry Keys: {list(entry.keys())}")
                    
                    # Only process user/assistant messages
                    if entry_type in ['user', 'assistant']:
                        message = entry.get('message', {})
                        role = message.get('role', 'unknown')
                        content = message.get('content', [])
                        
                        # Keep track of the latest UUID
                        if entry_uuid:
                            latest_uuid = entry_uuid
                        
                        # Extract text content - handle both string and array formats
                        text_parts = []
                        if isinstance(content, str):
                            # Simple string content
                            if content.strip():
                                text_parts.append(content)
                        elif isinstance(content, list):
                            # Array of content objects
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    text = item.get('text', '')
                                    if text.strip():
                                        text_parts.append(text)
                        
                        if text_parts:
                            full_text = ' '.join(text_parts).strip()
                            if full_text:
                                # Format message
                                if role == 'user':
                                    msg = f"👤 **User:** {full_text}"
                                else:
                                    msg = f"🤖 **Assistant:** {full_text}"
                                
                                conversation.append(msg)
                                
                                # In debug mode, show immediately
                                if debug_mode and not simple_mode:
                                    print(f"   {msg}")
                    
                    elif debug_mode and not simple_mode:
                        # Show other entry types in debug mode
                        print(f"📋 Entry type '{entry_type}': {json.dumps(entry, indent=2)[:500]}...")
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    if debug_mode:
                        print(f"⚠️  Processing Error: {e}")
                    continue
                    
    except FileNotFoundError:
        if debug_mode:
            print(f"❌ File not found: {transcript_path}")
    except Exception as e:
        if debug_mode:
            print(f"❌ Error reading file: {e}")
    
    # Output messages
    if simple_mode or not debug_mode:
        # In simple/normal mode, just output the messages
        for msg in conversation:
            print(msg)
    elif debug_mode and conversation:
        # In debug mode, show summary at end
        print("\n" + "=" * 80)
        print(f"💬 **Conversation Messages ({len(conversation)} new):**")
        for msg in conversation:
            print(msg)
    
    # Save the latest UUID if requested
    if last_message_file and latest_uuid:
        try:
            with open(last_message_file, 'w') as f:
                f.write(latest_uuid)
        except:
            pass

if __name__ == '__main__':
    main()