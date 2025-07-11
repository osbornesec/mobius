#!/bin/bash

# Enable strict error handling
# -e: Exit immediately if any command exits with non-zero status
# -u: Treat unset variables as an error and exit
# -o pipefail: Return value of a pipeline is the status of the last command to exit with non-zero status
set -euo pipefail

# Check each file passed as argument
for file in "$@"; do
  if [[ "$file" == *".env" && "$file" != *".env.sample" ]]; then
    echo "Error: Attempting to commit a .env file: $file" >&2
    echo "Please remove it from the commit and use .env.sample for templates." >&2
    exit 1
  fi
done

exit 0
