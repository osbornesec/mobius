#!/usr/bin/env python3

import sys
import os
from pathlib import Path

def main():
    commit_msg_filepath = sys.argv[1]
    session_file = Path.cwd() / ".claude" / "sessions" / ".current-session"

    if os.environ.get("SKIP_SESSION_COMMIT") == "1":
        return

    if not session_file.exists():
        return

    with open(session_file, "r") as f:
        session_content = f.read()

    with open(commit_msg_filepath, "w") as f:
        f.write("feat: Development session summary\n\n")
        f.write(session_content)

if __name__ == "__main__":
    main()