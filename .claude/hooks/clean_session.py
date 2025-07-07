#!/usr/bin/env python3
"""Extract only Mobius project work from session file"""

import re

# Patterns to identify Mobius project work
mobius_patterns = [
    r'ai_docs/tasks/\d+\.md',
    r'Phase \d+',
    r'Mobius.*project',
    r'architecture.*platform',
    r'Context Engineering Platform',
    r'FastAPI.*React.*TypeScript',
    r'Qdrant.*PostgreSQL',
    r'Multi-Agent.*System',
]

# Patterns to exclude (debugging work)
exclude_patterns = [
    r'extract_conversation\.py',
    r'log_tool_usage\.sh',
    r'\.claude/hooks/',
    r'\.current-session',
    r'\.last-message',
    r'duplicate',
    r'test message',
    r'This is a test',
    r'This is also a test',
    r'one more test',
    r'debugging',
    r'hook',
]

def should_include_section(section):
    """Check if a section should be included"""
    # Check if it contains Mobius patterns
    has_mobius = any(re.search(pattern, section, re.IGNORECASE) for pattern in mobius_patterns)
    
    # Check if it contains exclude patterns
    has_exclude = any(re.search(pattern, section, re.IGNORECASE) for pattern in exclude_patterns)
    
    return has_mobius and not has_exclude

def extract_mobius_content(input_file, output_file):
    """Extract only Mobius project content"""
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Split into sections (assuming ### marks section boundaries)
    sections = content.split('###')
    
    # Keep header if exists
    result = []
    if sections and not sections[0].strip().startswith('['):
        result.append(sections[0])
        sections = sections[1:]
    
    # Process each section
    for section in sections:
        if should_include_section(section):
            result.append('###' + section)
    
    # Write cleaned content
    with open(output_file, 'w') as f:
        f.write(''.join(result))
    
    print(f"Extracted {len(result)} sections containing Mobius project work")

if __name__ == '__main__':
    extract_mobius_content(
        '/home/michael/dev/Mobius/.claude/sessions/.current-session.backup',
        '/home/michael/dev/Mobius/.claude/sessions/.current-session'
    )