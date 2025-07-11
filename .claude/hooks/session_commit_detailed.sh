#!/bin/bash

# Enable strict error handling
# -e: Exit immediately if any command exits with non-zero status
# -u: Treat unset variables as an error and exit
# -o pipefail: Return value of a pipeline is the status of the last command to exit with non-zero status
set -euo pipefail

# Session Commit Detailed Script
# Purpose: Creates a git commit with a detailed summary of the current Claude session
# Usage: ./session_commit_detailed.sh
#
# This script will:
# - Extract a summary of work done from the current session file
# - Analyze staged files to determine commit scope
# - Create a formatted commit message with session details
# - Include file changes, conversation highlights, and session metadata

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
# Get the project root directory (assuming this script is in .claude/hooks/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SESSION_DIR="$PROJECT_ROOT/.claude/sessions"
SESSION_FILE="$SESSION_DIR/.current-session"

# Check if session file exists
if [ ! -f "$SESSION_FILE" ]; then
  echo -e "${RED}No active session found at $SESSION_FILE${NC}"
  exit 1
fi

# Check for staged changes
if ! git diff --cached --quiet; then
  echo -e "${GREEN}Found staged changes${NC}"
else
  echo -e "${RED}No changes staged for commit. Aborting.${NC}"
  exit 1
fi

# Get staged files for scope determination
STAGED_FILES=$(git diff --cached --name-only)

# Determine scope
SCOPE=""
if echo "$STAGED_FILES" | grep -q "^\.claude/hooks/"; then
  SCOPE="[hooks]"
elif echo "$STAGED_FILES" | grep -q "^\.claude/sessions/"; then
  SCOPE="[sessions]"
elif echo "$STAGED_FILES" | grep -q "^\.claude/commands/"; then
  SCOPE="[commands]"
elif echo "$STAGED_FILES" | grep -q "^\.claude/"; then
  SCOPE="[claude]"
else
  SCOPE="[project]"
fi

# Read session content
SESSION_CONTENT=$(cat "$SESSION_FILE")

# Generate AI summary of changes
# Additional delay to ensure session is fully captured
sleep 2

# Re-read session content after delay
SESSION_CONTENT=$(cat "$SESSION_FILE")

# Create a temporary file with staged changes
TEMP_DIFF="$(mktemp -t staged_changes_XXXXXX.diff)"
git diff --cached > "$TEMP_DIFF"

# Extract key changes from session file for context
# Use '|| true' to prevent grep from failing if no matches found
# Uncomment to include recent actions in the commit body
# RECENT_WORK=$(echo "$SESSION_CONTENT" | grep -E "(File Write|File Edit|File Read|Bash Command)" | tail -20 || true)
# Use the AI summary generator
AI_SUMMARY=$(echo "$SESSION_CONTENT" | python3 "$SCRIPT_DIR/generate_commit_summary.py" "$TEMP_DIFF" 2>/dev/null)

# Clean up temp file
rm -f "$TEMP_DIFF"

# Create a formatted commit message with AI summary and full session details
COMMIT_MESSAGE="$SCOPE $(echo "$AI_SUMMARY" | head -1)

Summary: $AI_SUMMARY

Session Details:
$(date +'Date: %Y-%m-%d %H:%M:%S')

=== SESSION TRANSCRIPT ===

$SESSION_CONTENT

=== END SESSION TRANSCRIPT ===

Files changed in this session:
$(echo "$STAGED_FILES" | sed 's/^/- /')

Session file: .current-session"

# Show preview
echo -e "\n${YELLOW}=== COMMIT MESSAGE PREVIEW ===${NC}"
echo -e "${BLUE}First 1000 characters:${NC}"
echo "----------------------------------------"
echo "${COMMIT_MESSAGE:0:1000}"
if [ ${#COMMIT_MESSAGE} -gt 1000 ]; then
  echo -e "\n${MAGENTA}... plus $(( ${#COMMIT_MESSAGE} - 1000 )) more characters${NC}"
fi
echo "----------------------------------------"

# Show statistics
echo -e "\n${YELLOW}Session Statistics:${NC}"
echo "- Total message size: ${#COMMIT_MESSAGE} characters"
echo "- Files modified: $(echo "$STAGED_FILES" | wc -l)"
echo "- Tool executions: $(grep -c "### \[" "$SESSION_FILE" 2>/dev/null || echo "0")"

# Warn about large commits
if [ ${#COMMIT_MESSAGE} -gt 50000 ]; then
  echo -e "\n${RED}WARNING: Large commit message (>50KB)${NC}"
  echo "Some git hosts may have limits on commit message size."
fi

# Get confirmation
echo -e "\n${GREEN}Create commit with full session transcript? (y/n):${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo -e "${RED}Commit aborted.${NC}"
  exit 1
fi

# Create temporary file for commit message (handles special characters better)
TEMP_FILE=$(mktemp)
echo "$COMMIT_MESSAGE" > "$TEMP_FILE"

# Create the commit
if git commit -F "$TEMP_FILE"; then
  echo -e "${GREEN}✓ Commit created successfully!${NC}"

  # Clean up temp file
  rm -f "$TEMP_FILE"

  # Archive the current session
  TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
  ARCHIVE_NAME="session_${TIMESTAMP}_committed.md"
  mkdir -p "$SESSION_DIR/archive"
  cp "$SESSION_FILE" "$SESSION_DIR/archive/$ARCHIVE_NAME"

  # Reset .current-session with a fresh session
  cat > "$SESSION_FILE" << EOF
# Development Session - $(date +'%Y-%m-%d %H:%M')

## Session Overview
- **Start Time**: $(date +'%B %d, %Y at %H:%M')
- **Project**: dev/Mobius
- **Working Directory**: $(pwd)
- **Previous Session**: Archived as $ARCHIVE_NAME

## Progress
EOF

  echo -e "\n${GREEN}✓ Session reset complete!${NC}"
  echo -e "- Session archived to: ${BLUE}archive/$ARCHIVE_NAME${NC}"
  echo -e "- New session started in: ${BLUE}.current-session${NC}"
  echo -e "\n${YELLOW}View the full commit with:${NC}"
  echo "  git show --format=fuller"
  echo "  git log -1 --format='%B'"
else
  echo -e "${RED}✗ Commit failed. Session not reset.${NC}"
  rm -f "$TEMP_FILE"
  exit 1
fi
