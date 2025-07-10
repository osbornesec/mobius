#!/usr/bin/env python3
"""Log tool usage and conversation to session file with sensitive data sanitization"""
import json
import sys
import os
import time
from datetime import datetime
import re
from pathlib import Path
import tempfile

# Dynamically determine paths based on script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Go up two levels: hooks -> .claude -> project root
SESSIONS_DIR = PROJECT_ROOT / ".claude" / "sessions"
SESSION_FILE_PATH = SESSIONS_DIR / ".current-session"

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

# Compile regex patterns once at module level for efficiency
COMPILED_PATTERNS = [(re.compile(pattern, re.IGNORECASE | re.MULTILINE), label) 
                     for pattern, label in SENSITIVE_PATTERNS]
COMBINED_SENSITIVE_REGEX = re.compile('|'.join(f'({pattern})' for pattern, _ in SENSITIVE_PATTERNS), re.IGNORECASE | re.MULTILINE)

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

# Pre-compute lowercase sensitive files list for better performance
SENSITIVE_FILES_LOWER = [f.lower() for f in SENSITIVE_FILES]

# Configure debug log path
def get_debug_log_path():
    """Get debug log path from environment or use default"""
    debug_path = os.environ.get('MOBIUS_DEBUG_LOG')
    if debug_path:
        return debug_path
    # Fallback to tempfile directory
    return os.path.join(tempfile.gettempdir(), 'hook_debug.log')

DEBUG_LOG_PATH = get_debug_log_path()

def sanitize_text(text):
    """Remove sensitive information from text"""
    if not text:
        return text
    
    # Create a replacer function that handles each match
    def replacer(match):
        # Find which pattern matched
        for regex, label in COMPILED_PATTERNS:
            if regex.match(match.group(0)):
                # Extract the sensitive value (first capturing group if exists)
                sensitive_value = match.group(1) if match.lastindex else match.group(0)
                
                if isinstance(sensitive_value, tuple):
                    sensitive_value = sensitive_value[0]
                
                # Handle None case (when capturing group exists but is empty)
                if sensitive_value is None:
                    sensitive_value = match.group(0)
                    
                if sensitive_value and len(sensitive_value) > 4:
                    # Show first 2 and last 2 characters for partial identification
                    replacement = f"[REDACTED-{label.upper()}:{sensitive_value[:2]}...{sensitive_value[-2:]}]"
                else:
                    replacement = f"[REDACTED-{label.upper()}]"
                
                # Replace only the sensitive part, preserving the rest of the match
                if match.lastindex and sensitive_value:
                    return match.group(0).replace(sensitive_value, replacement)
                else:
                    return replacement
        
        # This shouldn't happen if patterns are properly configured
        return match.group(0)
    
    # Combine all patterns into a single regex using alternation
    combined_pattern = '|'.join(f'({pattern})' for pattern, _ in SENSITIVE_PATTERNS)
    combined_regex = re.compile(combined_pattern, re.IGNORECASE | re.MULTILINE)
    
    # Apply all patterns in a single pass
    sanitized = combined_regex.sub(replacer, text)
    
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
    if file_name in SENSITIVE_FILES_LOWER:
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
    if not SESSION_FILE_PATH.exists():
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        with open(str(SESSION_FILE_PATH), 'w') as f:
            f.write(f"""# Development Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Session Overview
- **Start Time**: {datetime.now().strftime('%B %d, %Y at %H:%M')}
- **Project**: Mobius
- **Working Directory**: {PROJECT_ROOT}/

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

def extract_all_conversations(transcript_path, transcript_dir):
    """Extract conversation messages for ALL sessions found in transcript file"""
    from collections import defaultdict
    
    # Group data by session_id - this is the key improvement!
    sessions_data = defaultdict(lambda: {'processed_uuids': set(), 'conversation': [], 'new_uuids': []})
    
    # Load processed UUIDs for each session
    for session_file in os.listdir(transcript_dir):
        if session_file.startswith('.last-message-'):
            session_id = session_file.replace('.last-message-', '')
            processed_uuids_file = os.path.join(transcript_dir, session_file)
            
            try:
                with open(processed_uuids_file, 'r') as f:
                    for line in f:
                        uuid = line.strip()
                        if uuid:
                            sessions_data[session_id]['processed_uuids'].add(uuid)
            except (OSError, IOError) as e:
                # More specific exception handling as recommended by expert review
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(f"[{datetime.now()}] Error reading processed UUIDs from {processed_uuids_file}: {e}\n")
    
    try:
        with open(transcript_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    entry = json.loads(line)
                    
                    # Get session_id from the entry itself, not from input parameter
                    entry_session_id = entry.get('sessionId')
                    if not entry_session_id:
                        continue
                    
                    entry_uuid = entry.get('uuid')
                    entry_type = entry.get('type', 'unknown')
                    
                    # Skip if already processed for this session
                    if entry_uuid and entry_uuid in sessions_data[entry_session_id]['processed_uuids']:
                        continue
                    
                    # Track new UUID for this session (for ALL entry types)
                    if entry_uuid:
                        sessions_data[entry_session_id]['new_uuids'].append(entry_uuid)
                    
                    # Only process user/assistant messages for conversation extraction
                    if entry_type in ['user', 'assistant']:
                        message = entry.get('message', {})
                        role = message.get('role', 'unknown')
                        content = message.get('content', [])
                        
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
                                sessions_data[entry_session_id]['conversation'].append(msg)
                
                except json.JSONDecodeError as e:
                    # More specific exception handling as recommended by expert review
                    with open(DEBUG_LOG_PATH, 'a') as f:
                        f.write(f"[{datetime.now()}] JSON decode error in transcript: {e}\n")
                    continue
                except (OSError, IOError) as e:
                    with open(DEBUG_LOG_PATH, 'a') as f:
                        f.write(f"[{datetime.now()}] File error processing transcript line: {e}\n")
                    continue
                except Exception as e:
                    with open(DEBUG_LOG_PATH, 'a') as f:
                        f.write(f"[{datetime.now()}] Unexpected error processing transcript line: {e}\n")
                        import traceback
                        f.write(f"   Traceback: {traceback.format_exc()}\n")
                    continue
                    
    except (OSError, IOError) as e:
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] Error reading transcript file {transcript_path}: {e}\n")
    
    # Convert to regular dict and return
    return {session_id: (data['conversation'], data['new_uuids']) 
            for session_id, data in sessions_data.items() 
            if data['conversation'] or data['new_uuids']}

def main():
    """Main function to process and log tool usage"""
    
    # Always log that hook was called for debugging
    with open(DEBUG_LOG_PATH, 'a') as f:
        f.write(f"[{datetime.now()}] Hook called\n")
        # Log environment information that might help identify configuration source
        f.write(f"[{datetime.now()}] Script location: {__file__}\n")
        f.write(f"[{datetime.now()}] Working directory: {os.getcwd()}\n")
        f.write(f"[{datetime.now()}] PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}\n")
        # Log if we can find configuration files
        project_config = PROJECT_ROOT / ".claude" / "settings.json"
        global_config = Path.home() / ".claude" / "settings.json"
        f.write(f"[{datetime.now()}] Project config exists: {project_config.exists()}\n")
        f.write(f"[{datetime.now()}] Global config exists: {global_config.exists()}\n")
    
    # Initialize session file
    initialize_session_file()
    
    # Read JSON input from stdin
    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            # Log empty input for debugging
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(f"[{datetime.now()}] Empty stdin input\n")
            sys.exit(0)
            
        input_json = json.loads(stdin_data)
    except json.JSONDecodeError as e:
        # Log JSON parsing errors for debugging
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] JSON decode error: {e}\n")
            f.write(f"Input data: {repr(stdin_data[:200])}\n")
        sys.exit(1)
    except Exception as e:
        # Log other errors for debugging
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] Unexpected error: {e}\n")
        sys.exit(1)
    
    # Extract fields
    tool_name = input_json.get('tool_name', 'Unknown')
    tool_input = input_json.get('tool_input', {})
    tool_response = input_json.get('tool_response', {})
    session_id = input_json.get('session_id', '')
    transcript_path = input_json.get('transcript_path', '')
    
    # Debug log the extracted values
    with open(DEBUG_LOG_PATH, 'a') as f:
        f.write(f"[{datetime.now()}] tool_name='{tool_name}', session_id='{session_id}', transcript_path='{transcript_path}'\n")
        # Log if this session already has a .last-message file
        if session_id and transcript_path:
            transcript_dir = os.path.dirname(transcript_path)
            potential_last_message_file = f"{transcript_dir}/.last-message-{session_id}"
            has_last_message = os.path.exists(potential_last_message_file)
            f.write(f"[{datetime.now()}] Session {session_id} has existing .last-message file: {has_last_message}\n")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format tool entry with sanitization
    log_entry = format_tool_entry(tool_name, tool_input, tool_response, timestamp)
    
    # Get session-specific last message file - use same directory as transcript
    if session_id and transcript_path:
        transcript_dir = os.path.dirname(transcript_path)
        last_message_file = f"{transcript_dir}/.last-message-{session_id}"
        
        # Debug log the last message file path
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] Will create/update: {last_message_file}\n")
    else:
        # Log missing required fields for debugging
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] Missing required fields: session_id='{session_id}', transcript_path='{transcript_path}'\n")
        sys.exit(1)
    
    # Extract conversations for ALL sessions (we already verified we have required info above)
    conversation_text = ""
    transcript_dir = os.path.dirname(transcript_path)
    
    # If the provided transcript doesn't exist, find the session in other files
    if not os.path.exists(transcript_path):
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{datetime.now()}] WARNING: Transcript file doesn't exist: {transcript_path}\n")
            f.write(f"[{datetime.now()}] Searching for session {session_id} in all transcript files...\n")
        
        # Find which file(s) contain this session
        import glob
        found_in_files = []
        for jsonl_file in glob.glob(os.path.join(transcript_dir, "*.jsonl")):
            try:
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if line.strip() and f'"sessionId":"{session_id}"' in line:
                            found_in_files.append(jsonl_file)
                            break
            except Exception as e:
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(f"[{datetime.now()}] Error checking {jsonl_file}: {e}\n")
        
        if found_in_files:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(f"[{datetime.now()}] Found session {session_id} in: {found_in_files}\n")
            # Use the first file found (could be improved to handle multiple files)
            transcript_path = found_in_files[0]
        else:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(f"[{datetime.now()}] Session {session_id} not found in any transcript files!\n")
            # Exit early if session not found anywhere
            return
    
    if os.path.exists(transcript_path):
        # Use file locking to prevent race conditions - lock the transcript directory
        lock_file = f"{transcript_dir}/.extract_lock"
        
        try:
            # Try to acquire lock with timeout
            start_time = time.time()
            while os.path.exists(lock_file) and time.time() - start_time < 30:
                time.sleep(0.1)
            
            if os.path.exists(lock_file):
                raise OSError("Could not acquire lock")

            with open(lock_file, "w") as f:
                f.write(str(os.getpid()))
            
            try:
                # Extract conversations for ALL sessions found in transcript
                sessions_conversations = extract_all_conversations(transcript_path, transcript_dir)
                
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(f"[{datetime.now()}] Found {len(sessions_conversations)} sessions in transcript\n")
                
                # Process each session's conversation and update its .last-message file
                for session_id_found, (conversation, new_uuids) in sessions_conversations.items():
                    session_last_message_file = f"{transcript_dir}/.last-message-{session_id_found}"
                    
                    # Create .last-message file if it doesn't exist
                    if not os.path.exists(session_last_message_file):
                        with open(DEBUG_LOG_PATH, 'a') as f:
                            f.write(f"[{datetime.now()}] Creating new .last-message file: {session_last_message_file}\n")
                        with open(session_last_message_file, 'w') as f:
                            f.write("")  # Create empty file
                    
                    # Update processed UUIDs for this session
                    if new_uuids:
                        with open(DEBUG_LOG_PATH, 'a') as f:
                            f.write(f"[{datetime.now()}] Adding {len(new_uuids)} new UUIDs for session {session_id_found}\n")
                        with open(session_last_message_file, 'a') as f:
                            for uuid in new_uuids:
                                f.write(uuid + '\n')
                    
                    # If this is the current session, include conversation in session file
                    if session_id_found == session_id and conversation:
                        conversation_text = f"""

💬 **Recent Conversation:**
{chr(10).join(conversation)}"""
                            
            finally:
                # Release lock
                if os.path.exists(lock_file):
                    os.unlink(lock_file)
                
        except OSError:
            # Couldn't get lock, skip conversation to avoid duplicates
            conversation_text = "\n\n💬 **Recent Conversation:** [Skipped - concurrent access]"
    
    # Write everything to session file
    with open(str(SESSION_FILE_PATH), 'a') as f:
        f.write(log_entry)
        if conversation_text:
            f.write(conversation_text)
        f.write("\n")
    
    # Pass through the input unchanged
    print(json.dumps(input_json))

if __name__ == '__main__':
    main()