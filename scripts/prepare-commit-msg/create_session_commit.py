#!/usr/bin/env python3

import sys
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from sanitize import sanitize_text


def analyze_diff(diff_content):
    """Analyze git diff to understand changes"""
    changes = {
        "files_modified": set(),
        "files_added": set(),
        "files_deleted": set(),
        "functions_changed": set(),
        "imports_added": set(),
        "major_changes": [],
    }

    current_file = None
    for line in diff_content.split("\n"):
        # Track file changes
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                current_file = parts[2].replace("a/", "")

        elif line.startswith("new file mode"):
            if current_file:
                changes["files_added"].add(current_file)

        elif line.startswith("deleted file mode"):
            if current_file:
                changes["files_deleted"].add(current_file)

        elif line.startswith("+++") or line.startswith("---"):
            if (
                current_file
                and current_file not in changes["files_added"]
                and current_file not in changes["files_deleted"]
            ):
                changes["files_modified"].add(current_file)

        # Track function changes
        elif line.startswith("+def ") or line.startswith("-def "):
            func_match = re.match(r"[+-]def\s+(\w+)", line)
            if func_match:
                changes["functions_changed"].add(func_match.group(1))

        # Track import changes
        elif line.startswith("+import ") or line.startswith("+from "):
            changes["imports_added"].add(line[1:].strip())

    return changes


def analyze_session(session_content):
    """Analyze session content to understand what was done"""
    activities = {
        "files_written": [],
        "files_edited": [],
        "files_read": [],
        "commands_run": [],
        "todos_updated": [],
    }

    lines = session_content.split("\n")
    for i, line in enumerate(lines):
        if "File Write" in line and i + 2 < len(lines):
            file_match = re.search(r"\*\*File:\*\* `([^`]+)`", lines[i + 2])
            if file_match:
                activities["files_written"].append(file_match.group(1))

        elif "File Edit" in line and i + 2 < len(lines):
            file_match = re.search(r"\*\*File:\*\* `([^`]+)`", lines[i + 2])
            if file_match:
                activities["files_edited"].append(file_match.group(1))

        elif "Bash Command" in line and i + 2 < len(lines):
            cmd_match = re.search(r"\*\*Command:\*\* `([^`]+)`", lines[i + 2])
            if cmd_match:
                activities["commands_run"].append(cmd_match.group(1))

        elif "Todo Update" in line:
            activities["todos_updated"].append(line)

    return activities


def try_ai_summary(diff_content, session_content):
    """Try to generate summary using Google Gemini"""
    try:
        # Try multiple methods to get the API key
        api_key = None

        # Method 1: Check environment variable directly
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

        # Method 2: Try to use get_api_key.py script from multiple locations
        if not api_key:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "get_api_key.py"),
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    ".claude",
                    "hooks",
                    "get_api_key.py",
                ),
                os.path.join(
                    Path(__file__).resolve().parent.parent.parent,
                    ".claude",
                    "hooks",
                    "get_api_key.py",
                ),
            ]

            for api_key_script in possible_paths:
                if os.path.exists(api_key_script):
                    result = subprocess.run(
                        [sys.executable, api_key_script, "google"],
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(
                            api_key_script
                        ),  # Run from script's directory
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        api_key = result.stdout.strip()
                        break

        if api_key:
            # Use Google Gemini API
            import google.generativeai as genai
            from google.generativeai import types

            genai.configure(api_key=api_key)  # type: ignore
            model = genai.GenerativeModel("gemini-1.5-flash")  # type: ignore

            # Use raw diff content with size limit
            prompt_diff = diff_content[:3000] if diff_content else "No diff content"
            prompt = f"""Analyze these code changes and development session to write a detailed commit message.\n\nCode Changes:\n{prompt_diff}\n\nDevelopment Session Context:\n{session_content[-800:] if session_content else 'No session data'}\n\nWrite a comprehensive commit message that:\n- Uses a clear, descriptive title (50-72 characters)\n- Includes a detailed body explaining what was changed and why\n- Focuses on the technical purpose and business impact\n- Uses proper commit message format\n\nProvide only the commit message text (title + body if appropriate)."""
            response = model.generate_content(
                prompt,
                generation_config=types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                ),
                safety_settings=[
                    {
                        "category": types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": types.HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": types.HarmBlockThreshold.BLOCK_NONE,
                    },
                ],
            )

            # Response validation and error handling
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    # Check if content was blocked
                    if candidate.finish_reason in [2, "SAFETY"]:
                        return None

                # Try to access the text content safely
                try:
                    if hasattr(response, "text") and response.text:
                        return response.text.strip()
                    else:
                        return None
                except Exception:
                    return None
            else:
                return None
    except Exception:
        # Silently fail and fall back to rule-based summary
        pass

    return None


def generate_summary(diff_analysis, session_analysis):
    """Generate a concise summary based on the analyses"""
    summary_parts = []

    # Analyze the type of changes
    all_files = (
        diff_analysis["files_added"]
        | diff_analysis["files_modified"]
        | diff_analysis["files_deleted"]
    )

    # Categorize by file patterns
    categories = defaultdict(list)
    for file in all_files:
        if ".claude/hooks/" in file:
            categories["hooks"].append(file)
        elif "ai_docs/tasks/" in file:
            categories["tasks"].append(file)
        elif ".claude/sessions/" in file:
            categories["sessions"].append(file)
        elif "test" in file.lower():
            categories["tests"].append(file)
        elif file.endswith(".md"):
            categories["docs"].append(file)
        else:
            categories["other"].append(file)

    # Build summary based on categories
    if categories["hooks"]:
        hook_names = [
            f.split("/")[-1].replace(".py", "").replace(".sh", "")
            for f in categories["hooks"]
        ]
        summary_parts.append(f"Enhanced Claude hooks: {', '.join(hook_names[:3])}")

    if categories["tasks"]:
        task_count = len(categories["tasks"])
        summary_parts.append(f"Added {task_count} task definitions for Mobius platform")

    if categories["sessions"]:
        summary_parts.append("Improved session tracking and logging")

    if categories["tests"]:
        summary_parts.append(f"Added/updated {len(categories['tests'])} test files")

    if categories["docs"]:
        summary_parts.append(f"Updated documentation ({len(categories['docs'])} files)")

    # Add function-level changes if significant
    if len(diff_analysis["functions_changed"]) > 2:
        summary_parts.append(
            f"Refactored {len(diff_analysis['functions_changed'])} functions"
        )

    # If no specific categories, provide generic summary
    if not summary_parts:
        file_count = len(all_files)
        if file_count > 0:
            summary_parts.append(f"Updated {file_count} project files")
        else:
            summary_parts.append("Minor project updates")

    return ". ".join(summary_parts[:2])


def main():
    commit_msg_filepath = sys.argv[1]
    session_file = Path.cwd() / ".claude" / "sessions" / ".current-session"
    if os.environ.get("SKIP_SESSION_COMMIT") == "1":
        return
    if not session_file.exists():
        return
    with open(session_file, "r") as f:
        session_content = f.read()
    # Get git diff
    try:
        diff_content = subprocess.check_output(["git", "diff", "--staged"], text=True)
    except subprocess.CalledProcessError:
        diff_content = ""
    # Try AI-powered summary first
    summary = try_ai_summary(diff_content, session_content)
    if not summary:
        # Fall back to rule-based analysis
        diff_analysis = analyze_diff(diff_content)
        session_analysis = analyze_session(session_content)
        summary = generate_summary(diff_analysis, session_analysis)

    # Sanitize the session content before writing to the commit message
    sanitized_session_content = sanitize_text(session_content)

    with open(commit_msg_filepath, "w") as f:
        f.write(summary)
        f.write("\n\n")
        f.write(sanitized_session_content)


if __name__ == "__main__":
    main()
