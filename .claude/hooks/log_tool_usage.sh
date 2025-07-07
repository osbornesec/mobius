#!/bin/bash

# Always log to .current-session file
SESSION_FILE_PATH="/home/michael/dev/Mobius/.claude/sessions/.current-session"
LAST_MESSAGE_FILE="/home/michael/dev/Mobius/.claude/sessions/.last-message-id"

# Create sessions directory if it doesn't exist
mkdir -p "/home/michael/dev/Mobius/.claude/sessions"

# Initialize session file if it doesn't exist
if [ ! -f "$SESSION_FILE_PATH" ]; then
  cat > "$SESSION_FILE_PATH" << EOF
# Development Session - $(date +'%Y-%m-%d %H:%M')

## Session Overview
- **Start Time**: $(date +'%B %d, %Y at %H:%M')
- **Project**: Mobius
- **Working Directory**: /home/michael/dev/Mobius/

## Goals
[To be defined - What would you like to work on in this session?]

## Progress
EOF
fi

# Read the JSON input from stdin
INPUT_JSON=$(cat)

# Extract tool information using jq - fields are at top level
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // "Unknown"')
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Format based on tool type for better readability
case "$TOOL_NAME" in
  "Bash")
    COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // ""')
    DESCRIPTION=$(echo "$INPUT_JSON" | jq -r '.tool_input.description // ""')
    STDOUT=$(echo "$INPUT_JSON" | jq -r '.tool_response.stdout // ""')
    STDERR=$(echo "$INPUT_JSON" | jq -r '.tool_response.stderr // ""')
    
    LOG_ENTRY="
### [$TIMESTAMP] Bash Command

**Description:** $DESCRIPTION
**Command:** \`$COMMAND\`
**Output:**
\`\`\`
$STDOUT
\`\`\`"
    
    if [ -n "$STDERR" ]; then
      LOG_ENTRY="$LOG_ENTRY
**Error:**
\`\`\`
$STDERR
\`\`\`"
    fi
    ;;
    
  "Read")
    FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // ""')
    RESPONSE_FILE=$(echo "$INPUT_JSON" | jq -r '.tool_response.file.filePath // ""')
    NUM_LINES=$(echo "$INPUT_JSON" | jq -r '.tool_response.file.numLines // 0')
    
    LOG_ENTRY="
### [$TIMESTAMP] File Read

**File:** \`$FILE_PATH\`
**Lines:** $NUM_LINES"
    ;;
    
  "Write")
    FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // ""')
    CONTENT_LENGTH=$(echo "$INPUT_JSON" | jq -r '.tool_input.content | length // 0')
    
    LOG_ENTRY="
### [$TIMESTAMP] File Write

**File:** \`$FILE_PATH\`
**Size:** $CONTENT_LENGTH characters"
    ;;
    
  "Edit")
    FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // ""')
    OLD_STRING=$(echo "$INPUT_JSON" | jq -r '.tool_input.old_string // ""' | head -1)
    NEW_STRING=$(echo "$INPUT_JSON" | jq -r '.tool_input.new_string // ""' | head -1)
    
    LOG_ENTRY="
### [$TIMESTAMP] File Edit

**File:** \`$FILE_PATH\`
**Change:** Replaced \"${OLD_STRING:0:50}...\" with \"${NEW_STRING:0:50}...\""
    ;;
    
  "MultiEdit")
    FILE_PATH=$(echo "$INPUT_JSON" | jq -r '.tool_input.file_path // ""')
    NUM_EDITS=$(echo "$INPUT_JSON" | jq -r '.tool_input.edits | length // 0')
    
    LOG_ENTRY="
### [$TIMESTAMP] File MultiEdit

**File:** \`$FILE_PATH\`
**Edits:** $NUM_EDITS changes"
    ;;
    
  "TodoWrite")
    TODOS=$(echo "$INPUT_JSON" | jq -r '.tool_input.todos | length // 0')
    TODO_LIST=$(echo "$INPUT_JSON" | jq -r '.tool_input.todos[]? | "- [\(.status)] \(.content) (Priority: \(.priority))"')
    
    LOG_ENTRY="
### [$TIMESTAMP] Todo Update

**Action:** Updated $TODOS todo items

**Todos:**
$TODO_LIST"
    ;;
    
  *)
    # Generic format for other tools
    TOOL_INPUT=$(echo "$INPUT_JSON" | jq -c '.tool_input // {}')
    
    LOG_ENTRY="
### [$TIMESTAMP] $TOOL_NAME

**Input:** $TOOL_INPUT"
    ;;
esac

# Append to the session file
echo "$LOG_ENTRY" >> "$SESSION_FILE_PATH"

# For all tools, add conversation context with proper locking
if [[ "$TOOL_NAME" != "" ]]; then
  TRANSCRIPT_PATH=$(echo "$INPUT_JSON" | jq -r '.transcript_path // ""')
  SESSION_ID=$(echo "$INPUT_JSON" | jq -r '.session_id // ""')
  
  if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ] && [ -n "$SESSION_ID" ]; then
    # Use a lock file to prevent race conditions
    LOCK_FILE="$LAST_MESSAGE_FILE.lock"
    
    # Try to acquire lock (with timeout)
    if (set -C; echo $$ > "$LOCK_FILE") 2>/dev/null; then
      # We have the lock, extract conversation
      CONVERSATION=$(python3 /home/michael/dev/Mobius/.claude/hooks/extract_conversation.py "$TRANSCRIPT_PATH" "$SESSION_ID" --last-file "$LAST_MESSAGE_FILE" 2>/dev/null)
      
      if [ -n "$CONVERSATION" ]; then
        echo "" >> "$SESSION_FILE_PATH"
        echo "💬 **Recent Conversation:**" >> "$SESSION_FILE_PATH"
        echo "$CONVERSATION" >> "$SESSION_FILE_PATH"
      fi
      
      # Release the lock
      rm -f "$LOCK_FILE"
    else
      # Couldn't get lock, skip conversation context to avoid duplicates
      echo "" >> "$SESSION_FILE_PATH"
      echo "💬 **Recent Conversation:** [Skipped - concurrent access]" >> "$SESSION_FILE_PATH"
    fi
  fi
fi