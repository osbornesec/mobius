#!/usr/bin/env python3
"""Securely retrieve API keys for AI services"""

import os
import json
import sys
from pathlib import Path

def get_api_key(service='anthropic'):
    """
    Get API key from various sources in order of preference:
    1. Environment variables
    2. Local .env file
    3. Claude settings.json
    4. System keyring
    5. Config files
    """
    
    # 1. Check environment variables
    env_names = {
        'anthropic': ['ANTHROPIC_API_KEY', 'CLAUDE_API_KEY'],
        'openai': ['OPENAI_API_KEY'],
        'google': ['GOOGLE_API_KEY', 'GEMINI_API_KEY']
    }
    
    for env_var in env_names.get(service, []):
        key = os.environ.get(env_var)
        if key:
            return key
    
    # 2. Check .env file in various locations
    env_files = [
        Path(__file__).parent / '.env',  # hooks directory .env (highest priority)
        Path.cwd() / '.env',
        Path.home() / '.env',
        Path(__file__).parent.parent.parent / '.env'  # Project root
    ]
    
    for env_file in env_files:
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        for env_var in env_names.get(service, []):
                            if line.startswith(f"{env_var}="):
                                return line.split('=', 1)[1].strip('"\'')
            except:
                continue
    
    # 3. Check Claude's settings.json for API configurations
    claude_settings = Path.home() / '.claude' / 'settings.json'
    if claude_settings.exists():
        try:
            with open(claude_settings, 'r') as f:
                settings = json.load(f)
                # Check if API keys are stored in settings
                api_keys = settings.get('api_keys', {})
                if service in api_keys:
                    return api_keys[service]
        except:
            pass
    
    # 4. Check system keyring (if available)
    try:
        import keyring
        key = keyring.get_password(f"{service}_api", "key")
        if key:
            return key
    except ImportError:
        pass
    
    # 5. Check common config locations
    config_paths = [
        Path.home() / f'.{service}' / 'config.json',
        Path.home() / '.config' / service / 'config.json',
        Path.home() / f'.{service}rc'
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                if config_path.suffix == '.json':
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        if 'api_key' in config:
                            return config['api_key']
                else:
                    with open(config_path, 'r') as f:
                        for line in f:
                            if 'api_key' in line.lower():
                                return line.split('=', 1)[1].strip()
            except:
                continue
    
    return None

def save_api_key(service, api_key):
    """Save API key to .env file"""
    env_file = Path.cwd() / '.env'
    
    # Read existing content
    lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    
    # Update or add the API key
    env_var = f"{service.upper()}_API_KEY"
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith(f"{env_var}="):
            lines[i] = f"{env_var}={api_key}\n"
            updated = True
            break
    
    if not updated:
        lines.append(f"{env_var}={api_key}\n")
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    # Set restrictive permissions
    os.chmod(env_file, 0o600)
    
    print(f"API key saved to {env_file}")

if __name__ == '__main__':
    service = sys.argv[1] if len(sys.argv) > 1 else 'anthropic'
    
    api_key = get_api_key(service)
    if api_key:
        print(api_key)
    else:
        print(f"No API key found for {service}", file=sys.stderr)
        print(f"Please set {service.upper()}_API_KEY environment variable or create .env file", file=sys.stderr)
        sys.exit(1)