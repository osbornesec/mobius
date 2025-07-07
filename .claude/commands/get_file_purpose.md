# Get File Purpose

This command provides a high-level overview of a specified file's purpose and its role within the project. It helps in quickly understanding the context of a file without needing to read its entire content.

## Instructions

- Read the content of the specified `file_path`.
- Analyze the file's content, including comments, imports, function/class definitions, and overall structure.
- Based on the analysis, provide a concise summary (2-3 sentences) of the file's primary purpose and its contribution to the project.
- If the file is a `GEMINI.md` or `CLAUDE.md` file, summarize its directives.

## Parameters

- `file_path` (required): The absolute path to the file whose purpose needs to be determined.

## Example Usage

```
/get_file_purpose /home/michael/dev/Mobius/src/utils/helpers.js
/get_file_purpose /home/michael/dev/Mobius/tests/unit/auth.test.js
```
