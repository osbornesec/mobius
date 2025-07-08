#!/usr/bin/env python3
"""Log tool usage and conversation to session file with sensitive data sanitization"""
import json
import sys
import os
from datetime import datetime
import fcntl
import time
import re

SESSION_FILE_PATH = "/home/michael/dev/Mobius/.claude/sessions/.current-session"
SESSIONS_DIR = "/home/michael/dev/Mobius/.claude/sessions"

# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    # Passwords in various formats
    (r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password'),
    (r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password'),
    (r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password'),
    (r'pass["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'password'),
    (r'DATABASE_URL=([^\s]+)', 'database_url'),
    (r'postgres://[^@]+:([^@]+)@', 'db_password'),
    (r'mysql://[^@]+:([^@]+)@', 'db_password'),
    (r'mongodb://[^@]+:([^@]+)@', 'db_password'),
    
    # API keys and tokens
    (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'api_key'),
    (r'apikey["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'api_key'),
    (r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'token'),
    (r'auth[_-]?token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'auth_token'),
    (r'access[_-]?token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'access_token'),
    (r'refresh[_-]?token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'refresh_token'),
    (r'bearer\s+([^\s]+)', 'bearer_token'),
    
    # Secret keys
    (r'secret[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'secret_key'),
    (r'private[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'private_key'),
    (r'encryption[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'encryption_key'),
    
    # Cloud provider credentials
    (r'aws[_-]?access[_-]?key[_-]?id["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'aws_key'),
    (r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'aws_secret'),
    (r'GOOGLE[_-]?API[_-]?KEY["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'google_api_key'),
    (r'OPENAI[_-]?API[_-]?KEY["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'openai_api_key'),
    
    # SSH and certificates
    (r'-----BEGIN ([A-Z ]+)-----[\s\S]+?-----END \1-----', 'certificate'),
    (r'ssh-rsa\s+[A-Za-z0-9+/]+[=]{0,2}', 'ssh_key'),
    
    # Generic credentials
    (r'credentials["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'credentials'),
    (r'client[_-]?secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', 'client_secret'),
    
    # Environment variables that might contain secrets
    (r'POSTGRES_PASSWORD=([^\s]+)', 'postgres_password'),
    (r'REDIS_PASSWORD=([^\s]+)', 'redis_password'),
    (r'JWT_SECRET=([^\s]+)', 'jwt_secret'),
]

# Files that should never have their content logged
SENSITIVE_FILES = [
    '.env',
    '.env.local',
    '.env.production',
    '.env.development',
    'secrets.json',
    'credentials.json',
    'config/secrets.yml',
    'id_rsa',
    'id_dsa',
    'id_ecdsa',
    'id_ed25519',
    '.pem',
    '.key',
    '.pfx',
    '.p12',
]

def sanitize_text(text):
    """Remove sensitive information from text"""
    if not text:
        return text
    
    sanitized = text
    
    # Apply all sensitive patterns
    for pattern, label in SENSITIVE_PATTERNS:
        # Use case-insensitive matching
        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
        matches = regex.findall(sanitized)
        
        if matches:
            # Replace each match with redacted version
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match) > 4:
                    # Show first 2 and last 2 characters for partial identification
                    replacement = f"[REDACTED-{label.upper()}:{match[:2]}...{match[-2:]}]"
                else:
                    replacement = f"[REDACTED-{label.upper()}]"
                
                sanitized = sanitized.replace(match, replacement)
    
    # Also redact any line that contains common secret indicators
    lines = sanitized.split('\n')
    sanitized_lines = []
    
    for line in lines:
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in [
            'password', 'secret', 'api_key', 'apikey', 'token', 
            'private_key', 'credentials', 'auth'
        ]):
            # Check if the line might contain a value assignment
            if any(sep in line for sep in ['=', ':', '":', "':"]):
                # More aggressive redaction for these lines
                sanitized_lines.append(re.sub(r'([=:]\s*["\']?)([^"\'\s,}]+)(["\']?)', r'\1[REDACTED]\3', line))
            else:
                sanitized_lines.append(line)
        else:
            sanitized_lines.append(line)
    
    return '\n'.join(sanitized_lines)

def is_sensitive_file(file_path):
    """Check if a file is sensitive and shouldn't have content logged"""
    if not file_path:
        return False
    
    file_name = os.path.basename(file_path).lower()
    
    # Check exact matches
    if file_name in [f.lower() for f in SENSITIVE_FILES]:
        return True
    
    # Check extensions
    sensitive_extensions = ['.env', '.key', '.pem', '.pfx', '.p12']
    if any(file_name.endswith(ext) for ext in sensitive_extensions):
        return True
    
    # Check if file contains sensitive keywords
    sensitive_keywords = ['secret', 'credential', 'password', 'private', 'key']
    if any(keyword in file_name for keyword in sensitive_keywords):
        return True
    
    return False

def initialize_session_file():
    """Create session file if it doesn't exist"""
    if not os.path.exists(SESSION_FILE_PATH):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(SESSION_FILE_PATH, 'w') as f:
            f.write(f"""# Development Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Session Overview
- **Start Time**: {datetime.now().strftime('%B %d, %Y at %H:%M')}
- **Project**: Mobius
- **Working Directory**: /home/michael/dev/Mobius/

## Progress
""")

def format_tool_entry(tool_name, tool_input, tool_response, timestamp):
    """Format tool usage based on tool type with sanitization"""
    
    if tool_name == "Bash":
        command = sanitize_text(tool_input.get('command', ''))
        description = tool_input.get('description', '')
        stdout = sanitize_text(tool_response.get('stdout', ''))
        stderr = sanitize_text(tool_response.get('stderr', ''))
        
        entry = f"""
### [{timestamp}] Bash Command

**Description:** {description}
**Command:** `{command}`
**Output:**
```
{stdout}
```"""
        
        if stderr:
            entry += f"""
**Error:**
```
{stderr}
```"""
            
    elif tool_name == "Read":
        file_path = tool_input.get('file_path', '')
        num_lines = tool_response.get('file', {}).get('numLines', 0)
        
        # Check if this is a sensitive file
        if is_sensitive_file(file_path):
            entry = f"""
### [{timestamp}] File Read

**File:** `{file_path}`
**Status:** [SENSITIVE FILE - CONTENT NOT LOGGED]"""
        else:
            entry = f"""
### [{timestamp}] File Read

**File:** `{file_path}`
**Lines:** {num_lines}"""
        
    elif tool_name == "Write":
        file_path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')
        
        # Check if this is a sensitive file
        if is_sensitive_file(file_path):
            entry = f"""
### [{timestamp}] File Write

**File:** `{file_path}`
**Status:** [SENSITIVE FILE - CONTENT NOT LOGGED]"""
        else:
            # Still sanitize the content length display
            content_length = len(content)
            entry = f"""
### [{timestamp}] File Write

**File:** `{file_path}`
**Size:** {content_length} characters"""
        
    elif tool_name == "Edit":
        file_path = tool_input.get('file_path', '')
        
        if is_sensitive_file(file_path):
            entry = f"""
### [{timestamp}] File Edit

**File:** `{file_path}`
**Status:** [SENSITIVE FILE - CHANGES NOT LOGGED]"""
        else:
            old_string = sanitize_text(tool_input.get('old_string', '')[:50])
            new_string = sanitize_text(tool_input.get('new_string', '')[:50])
            
            entry = f"""
### [{timestamp}] File Edit

**File:** `{file_path}`
**Change:** Replaced "{old_string}..." with "{new_string}..." """
        
    elif tool_name == "MultiEdit":
        file_path = tool_input.get('file_path', '')
        num_edits = len(tool_input.get('edits', []))
        
        if is_sensitive_file(file_path):
            entry = f"""
### [{timestamp}] File MultiEdit

**File:** `{file_path}`
**Status:** [SENSITIVE FILE - CHANGES NOT LOGGED]"""
        else:
            entry = f"""
### [{timestamp}] File MultiEdit

**File:** `{file_path}`
**Edits:** {num_edits} changes"""
        
    elif tool_name == "TodoWrite":
        todos = tool_input.get('todos', [])
        todo_list = []
        for todo in todos:
            status = todo.get('status', 'unknown')
            content = sanitize_text(todo.get('content', ''))
            priority = todo.get('priority', 'medium')
            todo_list.append(f"- [{status}] {content} (Priority: {priority})")
        
        entry = f"""
### [{timestamp}] Todo Update

**Action:** Updated {len(todos)} todo items

**Todos:**
{chr(10).join(todo_list)}"""
        
    else:
        # Generic format for other tools - sanitize the JSON
        sanitized_input = json.dumps(tool_input, separators=(',', ':'))
        sanitized_input = sanitize_text(sanitized_input)
        
        entry = f"""
### [{timestamp}] {tool_name}

**Input:** {sanitized_input}"""
    
    return entry

def extract_conversation(transcript_path, session_id, processed_uuids_file):
    """Extract conversation messages that haven't been processed yet"""
    
    # Read previously processed UUIDs
    processed_uuids = set()
    if os.path.exists(processed_uuids_file):
        try:
            with open(processed_uuids_file, 'r') as f:
                for line in f:
                    uuid = line.strip()
                    if uuid:
                        processed_uuids.add(uuid)
        except:
            pass
    
    conversation = []
    new_uuids = []
    
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
                    
                    # Skip if already processed
                    if entry_uuid and entry_uuid in processed_uuids:
                        continue
                    
                    # Only process user/assistant messages
                    if entry_type in ['user', 'assistant']:
                        message = entry.get('message', {})
                        role = message.get('role', 'unknown')
                        content = message.get('content', [])
                        
                        # Track new UUID
                        if entry_uuid:
                            new_uuids.append(entry_uuid)
                        
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
                            # Sanitize conversation text
                            full_text = sanitize_text(full_text)
                            
                            if full_text:
                                if role == 'user':
                                    msg = f"👤 **User:** {full_text}"
                                else:
                                    msg = f"🤖 **Assistant:** {full_text}"
                                conversation.append(msg)
                
                except:
                    continue
                    
    except:
        pass
    
    return conversation, new_uuids

def main():
    """Main function to process and log tool usage"""
    
    # Initialize session file
    initialize_session_file()
    
    # Read JSON input from stdin
    try:
        input_json = json.loads(sys.stdin.read())
    except:
        sys.exit(0)
    
    # Extract fields
    tool_name = input_json.get('tool_name', 'Unknown')
    tool_input = input_json.get('tool_input', {})
    tool_response = input_json.get('tool_response', {})
    session_id = input_json.get('session_id', '')
    transcript_path = input_json.get('transcript_path', '')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format tool entry with sanitization
    log_entry = format_tool_entry(tool_name, tool_input, tool_response, timestamp)
    
    # Get session-specific last message file - use same directory as transcript
    if session_id and transcript_path:
        transcript_dir = os.path.dirname(transcript_path)
        last_message_file = f"{transcript_dir}/.last-message-{session_id}"
    else:
        # Exit early if we don't have required info for conversation extraction
        sys.exit(0)
    
    # Extract conversation (we already verified we have required info above)
    conversation_text = ""
    if os.path.exists(transcript_path):
        # Use file locking to prevent race conditions
        lock_file = f"{last_message_file}.lock"
        
        try:
            # Try to acquire lock with timeout
            lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            
            try:
                # Create .last-message file if it doesn't exist (for sessions without prior tool usage)
                if not os.path.exists(last_message_file):
                    with open(last_message_file, 'w') as f:
                        f.write("")  # Create empty file
                
                # Extract conversation
                conversation, new_uuids = extract_conversation(
                    transcript_path, session_id, last_message_file
                )
                
                if conversation:
                    conversation_text = f"""

💬 **Recent Conversation:**
{chr(10).join(conversation)}"""
                
                # Update processed UUIDs
                if new_uuids:
                    with open(last_message_file, 'a') as f:
                        for uuid in new_uuids:
                            f.write(uuid + '\n')
                            
            finally:
                # Release lock
                os.close(lock_fd)
                os.unlink(lock_file)
                
        except OSError:
            # Couldn't get lock, skip conversation to avoid duplicates
            conversation_text = "\n\n💬 **Recent Conversation:** [Skipped - concurrent access]"
    
    # Write everything to session file
    with open(SESSION_FILE_PATH, 'a') as f:
        f.write(log_entry)
        if conversation_text:
            f.write(conversation_text)
        f.write("\n")
    
    # Pass through the input unchanged
    print(json.dumps(input_json))

if __name__ == '__main__':
    main()