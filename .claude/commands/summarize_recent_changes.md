# Summarize Recent Changes

This command provides a concise summary of recent Git changes in the current repository. It's useful for quickly understanding what has been modified since the last commit or pull.

## Instructions

- Execute `git log --oneline --graph --max-count=10` to get a summary of the last 10 commits.
- If the user specifies a branch or commit hash, use `git log --oneline --graph --max-count=10 <branch_or_commit_hash>`.
- Summarize the key changes and affected files based on the log output.

## Parameters

- `branch_or_commit_hash` (optional): A specific Git branch name or commit hash to summarize changes from. If not provided, it defaults to the current branch.

## Example Usage

```
/summarize_recent_changes
/summarize_recent_changes main
/summarize_recent_changes develop
/summarize_recent_changes a1b2c3d4
```
