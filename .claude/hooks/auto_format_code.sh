#!/bin/bash

# Enable strict error handling
# -e: Exit immediately if any command exits with non-zero status
# -u: Treat unset variables as an error and exit
# -o pipefail: Return value of a pipeline is the status of the last command to exit with non-zero status
set -euo pipefail

# Read the hook input from stdin
HOOK_INPUT=$(cat)

# Extract the file_path using jq
FILE_PATH=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // ""')

# Exit if no file_path is found
if [ -z "$FILE_PATH" ] || [ "$FILE_PATH" == "null" ]; then
    exit 0
fi

# Check if prettier is installed
if ! command -v prettier &> /dev/null
then
    # If not installed, exit gracefully without an error
    exit 0
fi

# Run prettier on the file
prettier --write "$FILE_PATH" --log-level warn

# Always exit with 0 to not block the tool chain
exit 0
