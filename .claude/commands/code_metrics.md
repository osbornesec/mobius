# Code Metrics Analysis

Analyzes code quality metrics for both Python (backend) and JavaScript/TypeScript (frontend) code in the Mobius project.

## Command

```bash
# Python metrics (backend)
radon cc -s -a backend/
radon mi -s backend/
radon raw -s backend/
radon hal backend/

# JavaScript/TypeScript metrics (frontend)
npx complexity-report --format json frontend/src/
npx ts-complexity --threshold 10 frontend/src/

# Combined metrics with custom script
python scripts/analyze_metrics.py --path . --output metrics_report.json
```

## Parameters

- `--path`: Root directory to analyze (default: current directory)
- `--output`: Output file for metrics report (default: stdout)
- `--format`: Output format: json, html, markdown (default: json)
- `--threshold`: Complexity threshold for warnings (default: 10)
- `--exclude`: Comma-separated list of paths to exclude
- `--include-tests`: Include test files in analysis (default: false)
- `--coverage`: Include test coverage data if available

## Metrics Collected

### Code Volume Metrics
- **LOC**: Lines of Code (excluding comments and blanks)
- **SLOC**: Source Lines of Code (physical lines)
- **Comments**: Number of comment lines
- **Blanks**: Number of blank lines
- **Files**: Total number of files analyzed

### Complexity Metrics
- **Cyclomatic Complexity**: Number of linearly independent paths through code
- **Cognitive Complexity**: How difficult code is to understand
- **Halstead Metrics**: Volume, difficulty, effort, time, bugs
- **Maintainability Index**: Score from 0-100 (higher is better)

### Quality Indicators
- **Function Length**: Average and max lines per function
- **File Length**: Average and max lines per file
- **Duplication**: Percentage of duplicated code
- **Test Coverage**: Percentage of code covered by tests

## Setup

```bash
# Install Python analysis tools
pip install radon lizard flake8 pylint coverage

# Install JavaScript/TypeScript analysis tools
npm install -g complexity-report ts-complexity jscpd eslint

# Install additional tools
pip install pycomplexity
npm install -g plato code-complexity
```

## Usage Examples

### Basic Analysis
```bash
# Analyze Python backend
radon cc backend/ -a -s

# Analyze TypeScript frontend
npx ts-complexity frontend/src/ --threshold 15
```

### Comprehensive Report
```bash
# Generate full metrics report
python scripts/analyze_metrics.py \
  --path . \
  --output reports/metrics_$(date +%Y%m%d).json \
  --format json \
  --include-tests false \
  --coverage true
```

### Specific Module Analysis
```bash
# Python specific module
radon cc backend/api/endpoints/ -s -a
radon mi backend/api/endpoints/

# TypeScript specific component
npx complexity-report frontend/src/components/ContextBuilder/
```

### Duplication Detection
```bash
# Find duplicate code across project
jscpd . \
  --ignore "**/*.test.*,**/*.spec.*,**/node_modules/**,**/venv/**" \
  --format "json" \
  --output "duplication_report.json"
```

### Trend Analysis
```bash
# Compare metrics over time
python scripts/analyze_metrics.py --path . --trend --since "2024-01-01"
```

## Interpreting Results

### Cyclomatic Complexity
- **1-10**: Simple, low risk
- **11-20**: Moderate complexity, medium risk
- **21-50**: Complex, high risk
- **50+**: Very complex, very high risk

### Maintainability Index
- **0-9**: Very low maintainability
- **10-19**: Low maintainability
- **20-29**: Moderate maintainability
- **30+**: Good maintainability

### Recommended Thresholds
- Max function length: 50 lines
- Max file length: 300 lines
- Max cyclomatic complexity: 10
- Min test coverage: 80%
- Max duplication: 5%

## Integration with CI/CD

```yaml
# .github/workflows/code-metrics.yml
name: Code Metrics
on: [push, pull_request]

jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: |
          pip install radon lizard coverage
          npm install -g complexity-report ts-complexity jscpd
          
      - name: Run metrics analysis
        run: |
          python scripts/analyze_metrics.py \
            --path . \
            --output metrics.json \
            --threshold 10
            
      - name: Upload metrics
        uses: actions/upload-artifact@v3
        with:
          name: code-metrics
          path: metrics.json
```

## Custom Metrics Script

Create `scripts/analyze_metrics.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

def analyze_python_metrics(path):
    """Analyze Python code metrics using radon"""
    metrics = {}
    
    # Cyclomatic complexity
    cc_result = subprocess.run(
        ['radon', 'cc', '-s', '-j', str(path)],
        capture_output=True,
        text=True
    )
    metrics['complexity'] = json.loads(cc_result.stdout) if cc_result.returncode == 0 else {}
    
    # Maintainability index
    mi_result = subprocess.run(
        ['radon', 'mi', '-s', '-j', str(path)],
        capture_output=True,
        text=True
    )
    metrics['maintainability'] = json.loads(mi_result.stdout) if mi_result.returncode == 0 else {}
    
    # Raw metrics
    raw_result = subprocess.run(
        ['radon', 'raw', '-s', '-j', str(path)],
        capture_output=True,
        text=True
    )
    metrics['raw'] = json.loads(raw_result.stdout) if raw_result.returncode == 0 else {}
    
    return metrics

def analyze_typescript_metrics(path):
    """Analyze TypeScript/JavaScript metrics"""
    metrics = {}
    
    # Complexity report
    cr_result = subprocess.run(
        ['npx', 'complexity-report', '--format', 'json', str(path)],
        capture_output=True,
        text=True
    )
    
    if cr_result.returncode == 0:
        try:
            metrics['complexity'] = json.loads(cr_result.stdout)
        except json.JSONDecodeError:
            metrics['complexity'] = {'error': 'Failed to parse complexity report'}
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description='Analyze code metrics')
    parser.add_argument('--path', default='.', help='Path to analyze')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--format', default='json', choices=['json', 'html', 'markdown'])
    parser.add_argument('--threshold', type=int, default=10, help='Complexity threshold')
    parser.add_argument('--include-tests', action='store_true', help='Include test files')
    parser.add_argument('--coverage', action='store_true', help='Include coverage data')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    results = {
        'timestamp': datetime.now().isoformat(),
        'path': str(path.absolute()),
        'python': {},
        'typescript': {},
        'summary': {}
    }
    
    # Analyze Python backend
    backend_path = path / 'backend'
    if backend_path.exists():
        results['python'] = analyze_python_metrics(backend_path)
    
    # Analyze TypeScript frontend
    frontend_path = path / 'frontend' / 'src'
    if frontend_path.exists():
        results['typescript'] = analyze_typescript_metrics(frontend_path)
    
    # Generate summary
    results['summary'] = generate_summary(results, args.threshold)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))

def generate_summary(results, threshold):
    """Generate summary statistics"""
    summary = {
        'total_files': 0,
        'total_loc': 0,
        'high_complexity_functions': 0,
        'warnings': []
    }
    
    # Process Python metrics
    if 'raw' in results['python']:
        for file_data in results['python']['raw'].values():
            summary['total_files'] += 1
            summary['total_loc'] += file_data.get('loc', 0)
    
    if 'complexity' in results['python']:
        for file_path, file_data in results['python']['complexity'].items():
            for func in file_data:
                if func.get('complexity', 0) > threshold:
                    summary['high_complexity_functions'] += 1
                    summary['warnings'].append({
                        'type': 'high_complexity',
                        'file': file_path,
                        'function': func.get('name'),
                        'complexity': func.get('complexity')
                    })
    
    return summary

if __name__ == '__main__':
    main()
```

## Visualization

Generate visual reports using Plato (JavaScript) or radon (Python):

```bash
# JavaScript visualization with Plato
plato -r -d reports/plato frontend/src/

# Python visualization with radon
radon cc backend/ --show-complexity --total-average

# Generate complexity heatmap
python scripts/complexity_heatmap.py --input metrics.json --output heatmap.html
```

## Best Practices

1. **Regular Monitoring**: Run metrics analysis weekly to track trends
2. **Set Baselines**: Establish baseline metrics for your project
3. **Gradual Improvement**: Focus on improving the worst metrics first
4. **Team Standards**: Define and enforce team complexity thresholds
5. **Automated Checks**: Include metrics in CI/CD pipeline with fail conditions

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Install all required tools as shown in Setup
2. **Path errors**: Ensure paths are relative to project root
3. **Parser errors**: Some tools may fail on syntax errors - fix code first
4. **Performance**: Large codebases may take time - use --exclude for faster runs

### Debug Commands

```bash
# Verbose output
radon cc backend/ -s -a -v

# Check tool versions
radon --version
npx complexity-report --version

# Test on single file
radon cc backend/api/main.py -s
```