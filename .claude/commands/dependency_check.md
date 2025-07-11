# Dependency Check

This command performs comprehensive dependency analysis for both Python (backend) and JavaScript/TypeScript (frontend) components of the Mobius project. It checks for outdated packages, security vulnerabilities, and unused dependencies across the entire codebase.

## Instructions

1. **Detect Package Managers**: Automatically detect which package managers are in use by checking for:
   - Python: `requirements.txt`, `Pipfile`, `pyproject.toml`, `poetry.lock`
   - JavaScript/TypeScript: `package.json`, `yarn.lock`, `pnpm-lock.yaml`

2. **Run Dependency Checks**: Based on the detected package managers, execute appropriate checks:
   - **Outdated Dependencies**: List packages that have newer versions available
   - **Security Vulnerabilities**: Scan for known security issues
   - **Unused Dependencies**: Identify packages that are installed but not imported/used
   - **License Compliance**: Check for incompatible licenses

3. **Generate Report**: Compile results into a structured report with:
   - Summary statistics
   - Critical security vulnerabilities (if any)
   - Outdated packages grouped by severity (major/minor/patch)
   - Unused dependencies
   - Recommended actions

## Parameters

- `scope` (optional): Specify which part to check. Options: "backend", "frontend", "all" (default: "all")
- `check_type` (optional): Type of check to perform. Options: "outdated", "security", "unused", "licenses", "all" (default: "all")
- `fix` (optional): Automatically fix issues where possible (default: false)
- `output` (optional): Output format. Options: "console", "json", "markdown" (default: "console")

## Example Usage

```bash
# Check all dependencies across the entire project
/dependency_check

# Check only backend Python dependencies
/dependency_check --scope=backend

# Check only for security vulnerabilities
/dependency_check --check_type=security

# Check frontend dependencies and output as JSON
/dependency_check --scope=frontend --output=json

# Check and automatically update patch versions
/dependency_check --fix --check_type=outdated

# Generate a markdown report of all issues
/dependency_check --output=markdown > dependency_report.md
```

## Implementation Details

### Python Dependencies

**For pip/requirements.txt:**
```bash
# Check outdated packages
pip list --outdated

# Security check
pip-audit

# Find unused dependencies
pip-autoremove --list
```

**For Poetry:**
```bash
# Check outdated packages
poetry show --outdated

# Update dependencies
poetry update

# Check for vulnerabilities
poetry audit
```

**For Pipenv:**
```bash
# Check for security vulnerabilities
pipenv check

# Show outdated packages
pipenv update --outdated
```

### JavaScript/TypeScript Dependencies

**For npm:**
```bash
# Check outdated packages
npm outdated

# Security audit
npm audit

# Fix vulnerabilities
npm audit fix

# Find unused dependencies
npx depcheck
```

**For yarn:**
```bash
# Check outdated packages
yarn outdated

# Security audit
yarn audit

# Find unused dependencies
yarn dlx depcheck
```

**For pnpm:**
```bash
# Check outdated packages
pnpm outdated

# Security audit
pnpm audit

# Find unused dependencies
pnpm dlx depcheck
```

## Output Format Examples

### Console Output
```
Mobius Dependency Check Report
==============================
Checked at: 2024-01-15 10:30:00

BACKEND (Python)
----------------
✓ 45 dependencies checked
⚠ 8 outdated packages found
❌ 2 critical vulnerabilities detected
⚠ 3 unused dependencies

FRONTEND (JavaScript/TypeScript)
--------------------------------
✓ 132 dependencies checked
⚠ 15 outdated packages found
❌ 1 high severity vulnerability
⚠ 7 unused dependencies

RECOMMENDED ACTIONS:
1. Update critical security vulnerabilities immediately
2. Review and update major version changes
3. Remove unused dependencies to reduce attack surface
```

### JSON Output
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "backend": {
    "total": 45,
    "outdated": 8,
    "vulnerabilities": {
      "critical": 2,
      "high": 0,
      "medium": 3,
      "low": 1
    },
    "unused": 3
  },
  "frontend": {
    "total": 132,
    "outdated": 15,
    "vulnerabilities": {
      "critical": 0,
      "high": 1,
      "medium": 5,
      "low": 8
    },
    "unused": 7
  },
  "recommendations": [...]
}
```

## Notes

- Always run dependency checks in a virtual environment for Python projects
- Consider running these checks as part of CI/CD pipeline
- Some security scanners may require authentication tokens for enhanced scanning
- The `--fix` flag should be used cautiously in production environments
- Always review automatic updates before deploying to production
