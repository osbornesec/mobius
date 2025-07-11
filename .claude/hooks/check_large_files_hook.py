#!/usr/bin/env python3
import json
import sys
import os

MAX_FILE_SIZE_BYTES = 1024 * 1024 * 5  # 5 MB
BLOCKED_EXTENSIONS = [
    ".zip",
    ".tar.gz",
    ".mp4",
    ".mov",
    ".avi",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".pdf",
]


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Exit silently if input is not valid JSON

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Write":  # Only applies to new file writes
        sys.exit(0)

    file_path = input_data.get("tool_input", {}).get("file_path", "")
    content = input_data.get("tool_input", {}).get("content", "")

    if not file_path:
        sys.exit(0)

    file_extension = os.path.splitext(file_path)[1].lower()
    file_size = len(content.encode("utf-8"))  # Approximate size for text content

    if file_size > MAX_FILE_SIZE_BYTES:
        print(
            f"Warning: File '{file_path}' is large ({file_size / (1024*1024):.2f} MB). Consider using Git LFS or external storage for large files.",
            file=sys.stderr,
        )
        # sys.exit(2) # Uncomment to block large files

    if file_extension in BLOCKED_EXTENSIONS:
        print(
            f"Warning: Writing binary file '{file_path}'. Consider using Git LFS or external storage for binary assets.",
            file=sys.stderr,
        )
        # sys.exit(2) # Uncomment to block binary files

    sys.exit(0)


if __name__ == "__main__":
    main()
