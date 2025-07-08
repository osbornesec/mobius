#!/usr/bin/env python3
"""Generate an AI summary of git changes for commit messages"""

import sys
import re
import json
import os
import subprocess
from collections import defaultdict

def analyze_diff(diff_content):
    """Analyze git diff to understand changes"""
    changes = {
        'files_modified': set(),
        'files_added': set(),
        'files_deleted': set(),
        'functions_changed': set(),
        'imports_added': set(),
        'major_changes': []
    }
    
    current_file = None
    for line in diff_content.split('\n'):
        # Track file changes
        if line.startswith('diff --git'):
            parts = line.split()
            if len(parts) >= 3:
                current_file = parts[2].replace('a/', '')
        
        elif line.startswith('new file mode'):
            if current_file:
                changes['files_added'].add(current_file)
        
        elif line.startswith('deleted file mode'):
            if current_file:
                changes['files_deleted'].add(current_file)
        
        elif line.startswith('+++') or line.startswith('---'):
            if current_file and current_file not in changes['files_added'] and current_file not in changes['files_deleted']:
                changes['files_modified'].add(current_file)
        
        # Track function changes
        elif line.startswith('+def ') or line.startswith('-def '):
            func_match = re.match(r'[+-]def\s+(\w+)', line)
            if func_match:
                changes['functions_changed'].add(func_match.group(1))
        
        # Track import changes
        elif line.startswith('+import ') or line.startswith('+from '):
            changes['imports_added'].add(line[1:].strip())
    
    return changes

def analyze_session(session_content):
    """Analyze session content to understand what was done"""
    activities = {
        'files_written': [],
        'files_edited': [],
        'files_read': [],
        'commands_run': [],
        'todos_updated': []
    }
    
    lines = session_content.split('\n')
    for i, line in enumerate(lines):
        if 'File Write' in line and i + 2 < len(lines):
            file_match = re.search(r'\*\*File:\*\* `([^`]+)`', lines[i + 2])
            if file_match:
                activities['files_written'].append(file_match.group(1))
        
        elif 'File Edit' in line and i + 2 < len(lines):
            file_match = re.search(r'\*\*File:\*\* `([^`]+)`', lines[i + 2])
            if file_match:
                activities['files_edited'].append(file_match.group(1))
        
        elif 'Bash Command' in line and i + 2 < len(lines):
            cmd_match = re.search(r'\*\*Command:\*\* `([^`]+)`', lines[i + 2])
            if cmd_match:
                activities['commands_run'].append(cmd_match.group(1))
        
        elif 'Todo Update' in line:
            activities['todos_updated'].append(line)
    
    return activities

def try_ai_summary(diff_content, session_content):
    """Try to generate summary using Google Gemini"""
    print("DEBUG: Starting AI summary generation...", file=sys.stderr)
    try:
        # Try to get API key for Google/Gemini
        api_key_script = os.path.join(os.path.dirname(__file__), 'get_api_key.py')
        print(f"DEBUG: Looking for API key script at: {api_key_script}", file=sys.stderr)
        print(f"DEBUG: Script exists: {os.path.exists(api_key_script)}", file=sys.stderr)
        if os.path.exists(api_key_script):
            result = subprocess.run(
                [sys.executable, api_key_script, 'google'],
                capture_output=True,
                text=True
            )
            print(f"DEBUG: API key script result: {result.returncode}", file=sys.stderr)
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                print("DEBUG: API key obtained successfully", file=sys.stderr)
                
                # Use Google Gemini API
                print("DEBUG: Importing google.generativeai...", file=sys.stderr)
                import google.generativeai as genai
                
                print("DEBUG: Configuring genai...", file=sys.stderr)
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
                print("DEBUG: Model initialized", file=sys.stderr)
                
                # Use raw diff content with size limit
                prompt_diff = diff_content[:3000] if diff_content else "No diff content"
                
                prompt = f"""Analyze these code changes and development session to write a detailed commit message.

Code Changes:
{prompt_diff}

Development Session Context:
{session_content[-800:] if session_content else 'No session data'}

Write a comprehensive commit message that:
- Uses a clear, descriptive title (50-72 characters)
- Includes a detailed body explaining what was changed and why
- Focuses on the technical purpose and business impact
- Uses proper commit message format

Provide only the commit message text (title + body if appropriate)."""
                
                print("DEBUG: Generating content with Gemini...", file=sys.stderr)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=500,
                        temperature=0.3,
                    ),
                    safety_settings=[
                        {
                            "category": genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
                        },
                        {
                            "category": genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
                        },
                        {
                            "category": genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
                        },
                        {
                            "category": genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            "threshold": genai.types.HarmBlockThreshold.BLOCK_NONE,
                        },
                    ],
                    request_options={"timeout": 60}  # 60 second timeout
                )
                
                # Better response validation and error handling
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        print(f"DEBUG: Finish reason: {candidate.finish_reason}", file=sys.stderr)
                        
                        # Check if content was blocked
                        if candidate.finish_reason in [2, 'SAFETY']:  # 2 is SAFETY finish reason
                            print("DEBUG: Content blocked by safety filters", file=sys.stderr)
                            return None
                    
                    # Try to access the text content safely
                    try:
                        if hasattr(response, 'text') and response.text:
                            print(f"DEBUG: AI response received: '{response.text.strip()}'", file=sys.stderr)
                            return response.text.strip()
                        else:
                            print("DEBUG: No text content in response", file=sys.stderr)
                            return None
                    except Exception as text_error:
                        print(f"DEBUG: Error accessing response text: {text_error}", file=sys.stderr)
                        return None
                else:
                    print("DEBUG: No candidates in response", file=sys.stderr)
                    return None
    except Exception as e:
        # Log error for debugging
        print(f"DEBUG: AI summary failed with exception: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    return None

def generate_summary(diff_analysis, session_analysis):
    """Generate a concise summary based on the analyses"""
    summary_parts = []
    
    # Analyze the type of changes
    all_files = diff_analysis['files_added'] | diff_analysis['files_modified'] | diff_analysis['files_deleted']
    
    # Categorize by file patterns
    categories = defaultdict(list)
    for file in all_files:
        if '.claude/hooks/' in file:
            categories['hooks'].append(file)
        elif 'ai_docs/tasks/' in file:
            categories['tasks'].append(file)
        elif '.claude/sessions/' in file:
            categories['sessions'].append(file)
        elif 'test' in file.lower():
            categories['tests'].append(file)
        elif file.endswith('.md'):
            categories['docs'].append(file)
        else:
            categories['other'].append(file)
    
    # Build summary based on categories
    if categories['hooks']:
        hook_names = [f.split('/')[-1].replace('.py', '').replace('.sh', '') for f in categories['hooks']]
        summary_parts.append(f"Enhanced Claude hooks: {', '.join(hook_names[:3])}")
    
    if categories['tasks']:
        task_count = len(categories['tasks'])
        summary_parts.append(f"Added {task_count} task definitions for Mobius platform")
    
    if categories['sessions']:
        summary_parts.append("Improved session tracking and logging")
    
    if categories['tests']:
        summary_parts.append(f"Added/updated {len(categories['tests'])} test files")
    
    if categories['docs']:
        summary_parts.append(f"Updated documentation ({len(categories['docs'])} files)")
    
    # Add function-level changes if significant
    if len(diff_analysis['functions_changed']) > 2:
        summary_parts.append(f"Refactored {len(diff_analysis['functions_changed'])} functions")
    
    # If no specific categories, provide generic summary
    if not summary_parts:
        file_count = len(all_files)
        if file_count > 0:
            summary_parts.append(f"Updated {file_count} project files")
        else:
            summary_parts.append("Minor project updates")
    
    return '. '.join(summary_parts[:2])  # Limit to 2 main points

def main():
    # Read diff from file
    diff_file = sys.argv[1] if len(sys.argv) > 1 else '/tmp/staged_changes.diff'
    try:
        with open(diff_file, 'r') as f:
            diff_content = f.read()
    except:
        diff_content = ""
    
    # Read session content from stdin
    session_content = sys.stdin.read()
    
    # Try AI-powered summary first
    summary = try_ai_summary(diff_content, session_content)
    
    if not summary:
        print("DEBUG: AI summary failed, falling back to rule-based analysis", file=sys.stderr)
        # Fall back to rule-based analysis
        diff_analysis = analyze_diff(diff_content)
        session_analysis = analyze_session(session_content)
        summary = generate_summary(diff_analysis, session_analysis)
        print(f"DEBUG: Rule-based summary: '{summary}'", file=sys.stderr)
    else:
        print(f"DEBUG: Using AI summary: '{summary}'", file=sys.stderr)
    
    print(summary)

if __name__ == '__main__':
    main()