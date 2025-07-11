# Claude Code Review Configuration

This document explains the Claude Code Review workflow configuration and best
practices for the Mobius project.

## Overview

The Claude Code Review workflow automatically reviews pull requests using Claude
AI. However, due to token limitations, it has been configured to handle PRs
within certain size constraints.

## Size Limitations

The workflow will automatically skip review for PRs that exceed:

- **50 changed files**, OR
- **5,000 total line changes** (additions + deletions)

## Why These Limits?

Claude has a context window limit. Large PRs can cause:

- "Prompt is too long" errors
- Incomplete or failed reviews
- Workflow failures

## Best Practices

### 1. Keep PRs Small and Focused

- Aim for less than 20 files changed
- Target less than 1,000 lines changed
- Single, well-defined purpose

### 2. Split Large Changes

Break large features into multiple PRs:

- Separate backend and frontend changes
- Split infrastructure from business logic
- Isolate refactoring from new features
- Group related changes together

### 3. For Large PRs

If you must submit a large PR:

- Add `[skip-review]` to the PR title to skip automated review
- Use `@claude` mentions to request review of specific files/directories
- Request human review first

### 4. Manual Review Triggers

You can still use Claude for specific parts:

```bash
@claude review app/core/
@claude please check the security implications in auth.py
```

## Configuration Details

The workflow uses:

- `claude-sonnet-4` model by default
- Custom instructions for handling large PRs
- Automatic size checking before review attempt

## Troubleshooting

### "Prompt is too long" Error

This means your PR exceeded Claude's context limit. Solutions:

1. Wait for the skip message with instructions
1. Split the PR into smaller chunks
1. Use manual Claude triggers for specific files

### Review Not Triggering

Check if:

1. PR exceeds size limits (check workflow logs)
1. PR title contains `[skip-review]`
1. Workflow permissions are correct

## Future Improvements

Potential enhancements:

- Intelligent file sampling for large PRs
- Multi-pass review for different components
- Integration with other code review tools
