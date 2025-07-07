# Git Statistics Command

Analyze and visualize comprehensive Git repository statistics for the Mobius project.

## Overview

This command provides detailed insights into repository activity, contributor statistics, code evolution, and development patterns. It helps track project health, identify hotspots, and understand team dynamics.

## Usage

```bash
claude git_stats [options]
```

## Options

### Time Period Options
- `--period <value>`: Time period to analyze
  - `week`: Last 7 days
  - `month`: Last 30 days (default)
  - `quarter`: Last 90 days
  - `year`: Last 365 days
  - `all`: Entire repository history
  - `custom:<date1>..<date2>`: Custom date range (e.g., `custom:2024-01-01..2024-12-31`)

### Filter Options
- `--author <name>`: Filter by specific author(s) (comma-separated for multiple)
- `--branch <name>`: Analyze specific branch (default: current branch)
- `--path <path>`: Filter statistics to specific path/directory
- `--exclude <pattern>`: Exclude files matching pattern (e.g., `*.test.js`)

### Report Options
- `--format <type>`: Output format
  - `text`: Plain text report (default)
  - `markdown`: Markdown formatted report
  - `json`: JSON data for further processing
  - `html`: HTML report with charts
- `--output <file>`: Save report to file
- `--verbose`: Include detailed breakdowns
- `--charts`: Generate visual charts (requires matplotlib)

### Analysis Types
- `--type <analysis>`: Specific analysis to run (comma-separated for multiple)
  - `contributors`: Contributor statistics
  - `files`: File change frequency
  - `commits`: Commit patterns
  - `branches`: Branch activity
  - `churn`: Code churn analysis
  - `growth`: Repository growth metrics
  - `hotspots`: Code hotspot identification
  - `all`: Run all analyses (default)

## Examples

### Basic Statistics
```bash
# Get monthly statistics
claude git_stats

# Get statistics for the last week
claude git_stats --period week

# Get all-time statistics
claude git_stats --period all
```

### Contributor Analysis
```bash
# Analyze specific contributor
claude git_stats --author "John Doe" --period year

# Compare multiple contributors
claude git_stats --author "John Doe,Jane Smith" --type contributors

# Top contributors this quarter
claude git_stats --period quarter --type contributors --verbose
```

### Code Analysis
```bash
# Find most frequently changed files
claude git_stats --type files --verbose

# Analyze code churn in specific directory
claude git_stats --path src/backend --type churn

# Identify hotspots in the codebase
claude git_stats --type hotspots --period quarter
```

### Advanced Reports
```bash
# Generate HTML report with charts
claude git_stats --format html --charts --output stats_report.html

# Export data as JSON for custom analysis
claude git_stats --format json --output stats_data.json

# Comprehensive yearly report
claude git_stats --period year --type all --verbose --charts --format markdown --output yearly_report.md
```

### Custom Date Ranges
```bash
# Analyze specific date range
claude git_stats --period custom:2024-01-01..2024-06-30

# Compare before and after a release
claude git_stats --period custom:2024-05-01..2024-05-15 --type commits,churn
```

## Report Sections

### 1. Summary Statistics
- Total commits, contributors, and files
- Repository age and last activity
- Average commits per day/week/month
- Lines of code added/removed

### 2. Contributor Statistics
- Top contributors by commits/lines changed
- New contributors in period
- Contributor activity timeline
- Collaboration patterns

### 3. File Statistics
- Most frequently modified files
- Largest files by lines of code
- File type distribution
- Recently added/deleted files

### 4. Commit Patterns
- Commits by day of week/hour
- Commit message analysis
- Average commit size
- Merge vs. regular commits

### 5. Branch Analysis
- Active branches and their activity
- Branch creation/deletion patterns
- Long-lived branches
- Merge frequency

### 6. Code Churn
- Files with highest churn rate
- Churn by file type
- Refactoring indicators
- Stability metrics

### 7. Growth Metrics
- Repository size over time
- File count growth
- Lines of code evolution
- Technology adoption trends

### 8. Hotspot Analysis
- Files changed together frequently
- High-complexity areas with frequent changes
- Technical debt indicators
- Refactoring candidates

## Implementation Details

### Data Collection
```python
# Core statistics gathering
def collect_git_stats(repo_path, options):
    stats = {
        'commits': analyze_commits(options),
        'contributors': analyze_contributors(options),
        'files': analyze_files(options),
        'branches': analyze_branches(options),
        'churn': calculate_churn(options),
        'growth': track_growth(options)
    }
    return stats
```

### Visualization
```python
# Generate charts using matplotlib
def generate_charts(stats, output_format):
    if output_format == 'html':
        create_interactive_charts(stats)
    else:
        create_static_charts(stats)
```

### Performance Considerations
- Uses `git log --format` for efficient data extraction
- Implements caching for repeated analyses
- Parallel processing for large repositories
- Incremental updates for continuous monitoring

## Output Examples

### Text Output
```
=== Mobius Git Statistics Report ===
Period: Last 30 days (2024-11-15 to 2024-12-15)

Summary:
- Total Commits: 342
- Active Contributors: 12
- Files Changed: 189
- Lines Added: 15,234
- Lines Removed: 8,456

Top Contributors:
1. John Doe (124 commits, +5,234/-2,156)
2. Jane Smith (87 commits, +3,456/-1,234)
3. Bob Johnson (56 commits, +2,345/-987)

Most Changed Files:
1. src/backend/api/routes.py (45 changes)
2. src/frontend/components/Dashboard.tsx (32 changes)
3. tests/test_api.py (28 changes)

[... more sections ...]
```

### Markdown Output
```markdown
# Mobius Git Statistics Report

## Executive Summary
- **Period**: Last 30 days
- **Total Activity**: 342 commits across 189 files
- **Team Size**: 12 active contributors
- **Code Impact**: +15,234 / -8,456 lines

## Detailed Analysis

### Contributor Breakdown
| Contributor | Commits | Additions | Deletions | Impact |
|------------|---------|-----------|-----------|---------|
| John Doe   | 124     | 5,234     | 2,156     | High    |
| Jane Smith | 87      | 3,456     | 1,234     | High    |

[... more sections ...]
```

## Integration Points

### CI/CD Integration
```yaml
# .github/workflows/git-stats.yml
name: Weekly Git Stats
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
jobs:
  stats:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
        with:
          fetch-depth: 0  # Full history
      - name: Generate Stats
        run: |
          claude git_stats --period week --format markdown --output weekly_stats.md
          claude git_stats --period week --format html --charts --output weekly_stats.html
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: git-statistics
          path: |
            weekly_stats.md
            weekly_stats.html
```

### Monitoring Dashboard
- Real-time statistics updates
- Trend analysis and alerts
- Team performance metrics
- Code quality indicators

## Best Practices

1. **Regular Analysis**: Run weekly/monthly reports to track trends
2. **Focus Areas**: Use path filters to analyze specific components
3. **Team Reviews**: Share reports in team meetings for transparency
4. **Action Items**: Identify and address hotspots and high-churn areas
5. **Historical Data**: Maintain report archives for long-term analysis

## Troubleshooting

### Common Issues
- **Large Repository**: Use `--path` to limit scope or increase memory limits
- **Missing History**: Ensure full clone with `git fetch --unshallow`
- **Chart Generation**: Install matplotlib: `pip install matplotlib pandas`

### Performance Tips
- Use specific time periods instead of `--period all` for large repos
- Filter by path when analyzing specific components
- Enable caching with `--cache` flag for repeated runs

## Related Commands
- `claude code_review`: Review recent changes
- `claude project_stats`: Overall project metrics
- `claude contributor_insights`: Deep dive into contributor patterns