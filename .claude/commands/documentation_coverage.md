# Documentation Coverage Analysis

Analyzes documentation completeness across the Mobius project, including code documentation, API documentation, project documentation, and technical documentation.

## Usage

```bash
# Full documentation coverage analysis
claude run documentation_coverage

# Specific analysis types
claude run documentation_coverage --type code
claude run documentation_coverage --type api
claude run documentation_coverage --type project
claude run documentation_coverage --type technical

# Generate coverage report
claude run documentation_coverage --report
```

## Code Documentation Analysis

### Python Documentation (Backend)

#### 1. Docstring Style Check (pydocstyle)
```bash
# Install if needed
pip install pydocstyle

# Check all Python files for PEP 257 compliance
pydocstyle app/ --config=.pydocstyle.ini

# Check with specific conventions (Google, NumPy)
pydocstyle app/ --convention=google
pydocstyle app/ --convention=numpy

# Ignore specific errors
pydocstyle app/ --ignore=D100,D101,D102
```

#### 2. Docstring Coverage (interrogate)
```bash
# Install if needed
pip install interrogate

# Check docstring coverage
interrogate -v app/

# Generate detailed report
interrogate -v app/ --generate-badge ./docs/badges/

# Set minimum coverage threshold
interrogate -v app/ --fail-under 80

# Check specific components
interrogate -v app/api/ --fail-under 95
interrogate -v app/services/ --fail-under 90
interrogate -v app/models/ --fail-under 85
```

#### 3. Python Documentation Quality Checks
```python
# Custom script to check documentation quality
import ast
import os
from pathlib import Path

def check_function_documentation(filepath):
    """Check if functions have proper parameter and return documentation."""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            if docstring:
                # Check for parameter documentation
                for arg in node.args.args:
                    if arg.arg != 'self' and f':param {arg.arg}:' not in docstring:
                        issues.append(f"Missing param doc for {arg.arg} in {node.name}")

                # Check for return documentation
                if node.returns and ':return:' not in docstring:
                    issues.append(f"Missing return doc in {node.name}")

    return issues
```

### TypeScript/JavaScript Documentation (Frontend)

#### 1. TypeDoc Configuration
```json
// typedoc.json
{
    "$schema": "https://typedoc.org/schema.json",
    "entryPoints": ["src/index.ts"],
    "out": "docs/api",
    "validation": {
        "notExported": true,
        "invalidLink": true,
        "notDocumented": true
    },
    "requiredToBeDocumented": [
        "Enum",
        "Variable",
        "Function",
        "Class",
        "Interface",
        "Property",
        "Method",
        "TypeAlias"
    ],
    "coverage": {
        "threshold": 80
    }
}
```

#### 2. Generate TypeScript Documentation
```bash
# Install TypeDoc
npm install --save-dev typedoc

# Generate documentation
npx typedoc

# Check documentation coverage
npx typedoc --validation.notDocumented --showConfig

# Generate with coverage report
npx typedoc --plugin typedoc-plugin-coverage
```

#### 3. JSDoc/TSDoc Coverage Check
```javascript
// Custom coverage checker
const fs = require('fs');
const path = require('path');
const { Project } = require('ts-morph');

function checkTSDocCoverage(srcPath) {
    const project = new Project();
    project.addSourceFilesAtPaths(`${srcPath}/**/*.ts`);

    let total = 0;
    let documented = 0;

    project.getSourceFiles().forEach(sourceFile => {
        sourceFile.getClasses().forEach(classDecl => {
            total++;
            if (classDecl.getJsDocs().length > 0) documented++;

            classDecl.getMethods().forEach(method => {
                total++;
                if (method.getJsDocs().length > 0) documented++;
            });
        });

        sourceFile.getFunctions().forEach(func => {
            total++;
            if (func.getJsDocs().length > 0) documented++;
        });
    });

    return { total, documented, coverage: (documented / total) * 100 };
}
```

## API Documentation Analysis

### FastAPI Endpoint Documentation

#### 1. OpenAPI Schema Validation
```python
# Check FastAPI endpoint documentation
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import json

def check_api_documentation(app: FastAPI):
    """Validate OpenAPI schema completeness."""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    issues = []

    for path, methods in openapi_schema["paths"].items():
        for method, details in methods.items():
            # Check for description
            if not details.get("description"):
                issues.append(f"Missing description: {method.upper()} {path}")

            # Check for response documentation
            responses = details.get("responses", {})
            if "200" not in responses and "201" not in responses:
                issues.append(f"Missing success response doc: {method.upper()} {path}")

            # Check for error response documentation
            if "400" not in responses and "422" not in responses:
                issues.append(f"Missing error response doc: {method.upper()} {path}")

            # Check parameters
            if "parameters" in details:
                for param in details["parameters"]:
                    if not param.get("description"):
                        issues.append(f"Missing param description: {param['name']} in {method.upper()} {path}")

    return issues
```

#### 2. API Documentation Generation
```bash
# Generate ReDoc documentation
pip install fastapi[all]

# Export OpenAPI schema
python -c "
from app.main import app
import json
schema = app.openapi()
with open('docs/openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)
"

# Serve documentation
python -m http.server 8000 --directory docs/
```

### Request/Response Schema Documentation

```python
# Check Pydantic model documentation
from pydantic import BaseModel
import inspect
import importlib
import pkgutil

def check_schema_documentation(package_name):
    """Check if Pydantic models have proper documentation."""
    package = importlib.import_module(package_name)
    issues = []

    for importer, modname, ispkg in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        module = importlib.import_module(modname)

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseModel):
                # Check class docstring
                if not obj.__doc__:
                    issues.append(f"Missing docstring: {modname}.{name}")

                # Check field descriptions
                for field_name, field in obj.__fields__.items():
                    if not field.field_info.description:
                        issues.append(f"Missing field description: {modname}.{name}.{field_name}")

    return issues
```

## Project Documentation Analysis

### 1. README Completeness Check
```python
def check_readme_completeness(readme_path="README.md"):
    """Check if README contains essential sections."""
    required_sections = [
        "## Installation",
        "## Usage",
        "## Configuration",
        "## API Documentation",
        "## Contributing",
        "## License"
    ]

    optional_sections = [
        "## Architecture",
        "## Development",
        "## Testing",
        "## Deployment"
    ]

    with open(readme_path, 'r') as f:
        content = f.read()

    missing_required = [s for s in required_sections if s not in content]
    missing_optional = [s for s in optional_sections if s not in content]

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "has_badges": "![" in content,
        "has_examples": "```" in content,
        "word_count": len(content.split())
    }
```

### 2. Project Structure Documentation
```bash
# Generate project structure documentation
tree -I 'node_modules|__pycache__|*.pyc|.git' > docs/project_structure.md

# Check for missing documentation files
find . -type d -name "docs" | while read dir; do
    echo "Checking $dir"
    [ ! -f "$dir/README.md" ] && echo "  Missing: README.md"
    [ ! -f "$dir/API.md" ] && echo "  Missing: API.md"
    [ ! -f "$dir/ARCHITECTURE.md" ] && echo "  Missing: ARCHITECTURE.md"
done
```

### 3. Setup and Installation Guide Check
```python
def check_setup_documentation():
    """Verify setup documentation completeness."""
    files_to_check = [
        ("requirements.txt", ["fastapi", "pydantic", "sqlalchemy"]),
        ("package.json", ["react", "typescript", "@types/react"]),
        ("docker-compose.yml", ["services", "volumes", "networks"]),
        (".env.example", ["DATABASE_URL", "API_KEY", "SECRET_KEY"])
    ]

    issues = []
    for filepath, required_content in files_to_check:
        if not os.path.exists(filepath):
            issues.append(f"Missing file: {filepath}")
        else:
            with open(filepath, 'r') as f:
                content = f.read()
                for req in required_content:
                    if req not in content:
                        issues.append(f"Missing in {filepath}: {req}")

    return issues
```

## Technical Documentation Analysis

### 1. Architecture Decision Records (ADRs)
```bash
# Check for ADRs
ADR_DIR="docs/adr"
if [ -d "$ADR_DIR" ]; then
    echo "Found ADRs:"
    ls -la "$ADR_DIR"/*.md | wc -l

    # Check ADR format
    for adr in "$ADR_DIR"/*.md; do
        if ! grep -q "## Status" "$adr"; then
            echo "Missing Status section: $adr"
        fi
        if ! grep -q "## Context" "$adr"; then
            echo "Missing Context section: $adr"
        fi
        if ! grep -q "## Decision" "$adr"; then
            echo "Missing Decision section: $adr"
        fi
        if ! grep -q "## Consequences" "$adr"; then
            echo "Missing Consequences section: $adr"
        fi
    done
else
    echo "No ADR directory found"
fi
```

### 2. Database Documentation
```python
# Check database schema documentation
from sqlalchemy import create_engine, inspect

def check_database_documentation(database_url):
    """Check if database tables and columns are documented."""
    engine = create_engine(database_url)
    inspector = inspect(engine)

    undocumented = []

    for table_name in inspector.get_table_names():
        # Check for table comment
        table_comment = inspector.get_table_comment(table_name)
        if not table_comment['text']:
            undocumented.append(f"Table {table_name}: No comment")

        # Check column comments
        for column in inspector.get_columns(table_name):
            if not column.get('comment'):
                undocumented.append(f"Column {table_name}.{column['name']}: No comment")

    return undocumented
```

### 3. Configuration Documentation
```python
def check_config_documentation():
    """Verify all configuration options are documented."""
    config_files = [
        ".env.example",
        "config/default.json",
        "config/production.json"
    ]

    env_vars = set()

    # Collect all environment variables from code
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                    # Find os.environ references
                    import re
                    env_refs = re.findall(r'os\.environ\.get\(["\'](\w+)["\']', content)
                    env_vars.update(env_refs)

    # Check if documented
    documented = set()
    if os.path.exists(".env.example"):
        with open(".env.example", 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    var_name = line.split('=')[0].strip()
                    documented.add(var_name)

    undocumented = env_vars - documented
    return list(undocumented)
```

### 4. Deployment Documentation Check
```bash
# Check deployment documentation
echo "Checking deployment documentation..."

# Required deployment docs
required_docs=(
    "docs/deployment/README.md"
    "docs/deployment/docker.md"
    "docs/deployment/kubernetes.md"
    "docs/deployment/monitoring.md"
    "docs/deployment/troubleshooting.md"
)

for doc in "${required_docs[@]}"; do
    if [ ! -f "$doc" ]; then
        echo "Missing: $doc"
    else
        # Check content
        word_count=$(wc -w < "$doc")
        if [ "$word_count" -lt 100 ]; then
            echo "Insufficient content in $doc (only $word_count words)"
        fi
    fi
done
```

## Coverage Report Generation

```python
#!/usr/bin/env python3
"""Generate comprehensive documentation coverage report."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def generate_coverage_report():
    """Generate a comprehensive documentation coverage report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "Mobius",
        "coverage": {}
    }

    # Python docstring coverage
    try:
        result = subprocess.run(
            ["interrogate", "-v", "app/", "--quiet"],
            capture_output=True,
            text=True
        )
        coverage_line = [l for l in result.stdout.split('\n') if 'TOTAL' in l][0]
        coverage_percent = float(coverage_line.split()[-1].replace('%', ''))
        report["coverage"]["python_docstrings"] = coverage_percent
    except:
        report["coverage"]["python_docstrings"] = "N/A"

    # TypeScript documentation coverage
    try:
        # Run TypeDoc with coverage plugin
        subprocess.run(["npx", "typedoc", "--plugin", "typedoc-plugin-coverage"])
        # Parse coverage report
        if Path("docs/api/coverage.json").exists():
            with open("docs/api/coverage.json", 'r') as f:
                ts_coverage = json.load(f)
                report["coverage"]["typescript"] = ts_coverage["percent"]
    except:
        report["coverage"]["typescript"] = "N/A"

    # API documentation coverage
    api_issues = check_api_documentation_coverage()
    report["coverage"]["api_endpoints"] = {
        "documented": api_issues["documented"],
        "total": api_issues["total"],
        "percent": (api_issues["documented"] / api_issues["total"]) * 100
    }

    # Project documentation
    project_docs = check_project_documentation()
    report["coverage"]["project_docs"] = project_docs

    # Generate HTML report
    generate_html_report(report)

    # Generate markdown report
    generate_markdown_report(report)

    return report

def generate_html_report(report):
    """Generate an HTML coverage report."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mobius Documentation Coverage Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .coverage {{ margin: 20px 0; }}
            .good {{ color: green; }}
            .warning {{ color: orange; }}
            .bad {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Documentation Coverage Report</h1>
        <p>Generated: {report['timestamp']}</p>

        <div class="coverage">
            <h2>Coverage Summary</h2>
            <table>
                <tr>
                    <th>Component</th>
                    <th>Coverage</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Python Docstrings</td>
                    <td>{report['coverage']['python_docstrings']}%</td>
                    <td class="{get_status_class(report['coverage']['python_docstrings'])}">
                        {get_status_emoji(report['coverage']['python_docstrings'])}
                    </td>
                </tr>
                <tr>
                    <td>TypeScript Documentation</td>
                    <td>{report['coverage']['typescript']}%</td>
                    <td class="{get_status_class(report['coverage']['typescript'])}">
                        {get_status_emoji(report['coverage']['typescript'])}
                    </td>
                </tr>
            </table>
        </div>

        <div class="recommendations">
            <h2>Recommendations</h2>
            <ul>
                {generate_recommendations(report)}
            </ul>
        </div>
    </body>
    </html>
    """

    with open("docs/coverage_report.html", 'w') as f:
        f.write(html)

def get_status_class(coverage):
    """Get CSS class based on coverage percentage."""
    if isinstance(coverage, str):
        return "warning"
    if coverage >= 80:
        return "good"
    elif coverage >= 60:
        return "warning"
    else:
        return "bad"

def get_status_emoji(coverage):
    """Get status emoji based on coverage percentage."""
    if isinstance(coverage, str):
        return "⚠️"
    if coverage >= 80:
        return "✅"
    elif coverage >= 60:
        return "⚠️"
    else:
        return "❌"
```

## Automation Script

```bash
#!/bin/bash
# documentation_coverage.sh - Run all documentation coverage checks

set -e

echo "🔍 Mobius Documentation Coverage Analysis"
echo "========================================"

# Create reports directory
mkdir -p docs/reports

# Python documentation
echo -e "\n📚 Checking Python Documentation..."
if command -v interrogate &> /dev/null; then
    interrogate -v app/ --generate-badge docs/badges/
else
    echo "⚠️  interrogate not installed. Run: pip install interrogate"
fi

if command -v pydocstyle &> /dev/null; then
    pydocstyle app/ --count || true
else
    echo "⚠️  pydocstyle not installed. Run: pip install pydocstyle"
fi

# TypeScript documentation
echo -e "\n📘 Checking TypeScript Documentation..."
if [ -f "package.json" ]; then
    npx typedoc --showConfig || echo "⚠️  TypeDoc not configured"
fi

# API documentation
echo -e "\n🌐 Checking API Documentation..."
python -c "
from app.main import app
print(f'Total endpoints: {len(app.routes)}')
print(f'OpenAPI schema generated: {bool(app.openapi_schema)}')
"

# Project documentation
echo -e "\n📄 Checking Project Documentation..."
for file in README.md CONTRIBUTING.md LICENSE; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

# Generate report
echo -e "\n📊 Generating Coverage Report..."
python generate_coverage_report.py

echo -e "\n✨ Documentation coverage analysis complete!"
echo "📋 Report available at: docs/coverage_report.html"
```

## Configuration Files

### .pydocstyle.ini
```ini
[pydocstyle]
inherit = false
match = .*\.py
match-dir = ^(?!migrations|tests|__pycache__).*
convention = google
add-ignore = D100,D104,D106
```

### .interrogate.yaml
```yaml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = false
ignore-magic = false
ignore-semiprivate = false
ignore-private = false
ignore-property-decorators = false
ignore-module = false
fail-under = 80
exclude = ["tests", "migrations"]
ignore-regex = ["^get$", "^mock_.*", ".*BaseClass.*"]
verbose = 2
quiet = false
whitelist-regex = []
color = true
```

## VS Code Integration

```json
// .vscode/settings.json
{
    "python.linting.pydocstyleEnabled": true,
    "python.linting.pydocstyleArgs": [
        "--convention=google"
    ],
    "typescript.preferences.includePackageJsonAutoImports": "on",
    "typescript.tsdk": "node_modules/typescript/lib",
    "typedoc.entryPoints": ["src/index.ts"],
    "editor.quickSuggestions": {
        "comments": true
    }
}
```

## GitHub Actions Integration

```yaml
# .github/workflows/documentation.yml
name: Documentation Coverage

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  doc-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Python dependencies
        run: |
          pip install interrogate pydocstyle

      - name: Check Python documentation
        run: |
          interrogate -v app/ --fail-under 80
          pydocstyle app/ --convention=google

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Node dependencies
        run: npm ci

      - name: Check TypeScript documentation
        run: npx typedoc --validation.notDocumented

      - name: Upload coverage report
        uses: actions/upload-artifact@v3
        with:
          name: documentation-coverage
          path: docs/coverage_report.html
```
