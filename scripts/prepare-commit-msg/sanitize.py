#!/usr/bin/env python3

import re

# Sensitive patterns to redact
SENSITIVE_PATTERNS = [
    # Passwords in various formats
    (r'password["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "password"),
    (r'passwd["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "password"),
    (r'pwd["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "password"),
    (r'pass["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "password"),
    (r"DATABASE_URL=([^\s]+)", "database_url"),
    (r"postgres://[^@]+:([^@]+)@", "db_password"),
    (r"mysql://[^@]+:([^@]+)@", "db_password"),
    (r"mongodb://[^@]+:([^@]+)@", "db_password"),
    # API keys and tokens
    (r'api[_-]?key["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "api_key"),
    (r'apikey["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "api_key"),
    (r'token["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "token"),
    (r'auth[_-]?token["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "auth_token"),
    (r'access[_-]?token["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "access_token"),
    (
        r'refresh[_-]?token["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "refresh_token",
    ),
    (r"bearer\s+([^\s]+)", "bearer_token"),
    # Secret keys
    (r'secret[_-]?key["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "secret_key"),
    (r'private[_-]?key["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "private_key"),
    (
        r'encryption[_-]?key["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "encryption_key",
    ),
    # Cloud provider credentials
    (
        r'aws[_-]?access[_-]?key[_-]?id["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "aws_key",
    ),
    (
        r'aws[_-]?secret[_-]?access[_-]?key["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "aws_secret",
    ),
    (
        r'GOOGLE[_-]?API[_-]?KEY["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "google_api_key",
    ),
    (
        r'OPENAI[_-]?API[_-]?KEY["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "openai_api_key",
    ),
    # SSH and certificates
    (r'-----BEGIN ([A-Z ]+)-----["\\]s\S]+?-----END \1-----', "certificate"),
    (r"ssh-rsa\s+[A-Za-z0-9+/]+[=]{0,2}", "ssh_key"),
    # Generic credentials
    (r'credentials["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)', "credentials"),
    (
        r'client[_-]?secret["\\]?\\]?\s*[:=]\s*["\\]?\\]?([^"\\\]?\s,}]+)',
        "client_secret",
    ),
    # Environment variables that might contain secrets
    (r"POSTGRES_PASSWORD=([^\s]+)", "postgres_password"),
    (r"REDIS_PASSWORD=([^\s]+)", "redis_password"),
    (r"JWT_SECRET=([^\s]+)", "jwt_secret"),
]

# Compile regex patterns once at module level for efficiency
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE | re.MULTILINE), label)
    for pattern, label in SENSITIVE_PATTERNS
]


def sanitize_text(text):
    """Remove sensitive information from text"""
    if not text:
        return text

    # Create a replacer function that handles each match
    def replacer(match):
        # Find which pattern matched
        for regex, label in COMPILED_PATTERNS:
            if regex.match(match.group(0)):
                # Extract the sensitive value (first capturing group if exists)
                sensitive_value = match.group(1) if match.lastindex else match.group(0)

                if isinstance(sensitive_value, tuple):
                    sensitive_value = sensitive_value[0]

                # Handle None case (when capturing group exists but is empty)
                if sensitive_value is None:
                    sensitive_value = match.group(0)

                if sensitive_value and len(sensitive_value) > 4:
                    # Show first 2 and last 2 characters for partial identification
                    replacement = f"[REDACTED-{label.upper()}:{sensitive_value[:2]}...{sensitive_value[-2:]}]"
                else:
                    replacement = f"[REDACTED-{label.upper()}]"

                # Replace only the sensitive part, preserving the rest of the match
                if match.lastindex and sensitive_value:
                    return match.group(0).replace(sensitive_value, replacement)
                else:
                    return replacement

        # This shouldn't happen if patterns are properly configured
        return match.group(0)

    # Combine all patterns into a single regex using alternation
    combined_pattern = "|".join(f"({pattern})" for pattern, _ in SENSITIVE_PATTERNS)
    combined_regex = re.compile(combined_pattern, re.IGNORECASE | re.MULTILINE)

    # Apply all patterns in a single pass
    sanitized = combined_regex.sub(replacer, text)

    # Also redact any line that contains common secret indicators
    lines = sanitized.split("\n")
    sanitized_lines = []

    for line in lines:
        line_lower = line.lower()
        if any(
            indicator in line_lower
            for indicator in [
                "password",
                "secret",
                "api_key",
                "apikey",
                "token",
                "private_key",
                "credentials",
                "auth",
            ]
        ):
            # Check if the line might contain a value assignment
            if any(sep in line for sep in ["=", ":", '":', "':"]):
                # More aggressive redaction for these lines
                sanitized_lines.append(
                    re.sub(
                        r'([=:]\s*["\\]?\\]?)([^"\\\]?\s,}]+)(["\\]?\\]?)',
                        r"\\1[REDACTED]\\3",
                        line,
                    )
                )
            else:
                sanitized_lines.append(line)
        else:
            sanitized_lines.append(line)

    return "\n".join(sanitized_lines)
