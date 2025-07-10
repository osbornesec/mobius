#!/bin/bash

for file in "$@"; do
  if [[ "$file" == *".env" && "$file" != *".env.sample" ]]; then
    echo "Error: Attempting to commit a .env file: $file" >&2
    echo "Please remove it from the commit and use .env.sample for templates." >&2
    exit 1
  fi
done

exit 0
