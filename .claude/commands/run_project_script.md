# Run Project Script

This command provides a convenient shortcut to execute common project-specific scripts (e.g., build, test, lint) defined in `package.json` or other project configuration files. It abstracts away the exact shell command, allowing for simpler execution.

## Instructions

- Read the `package.json` file (or other relevant project configuration files like `Makefile`, `pyproject.toml`, etc.) to identify available scripts.
- Execute the script corresponding to the provided `script_name`.
- Pass any additional `args` directly to the script.
- Report the output of the script.

## Parameters

- `script_name` (required): The name of the script to run (e.g., "test", "build", "lint").
- `args` (optional): Additional arguments to pass to the script.

## Example Usage

```
/run_project_script test
/run_project_script build --production
/run_project_script lint --fix src/
```
