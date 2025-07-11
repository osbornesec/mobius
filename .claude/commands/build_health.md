# Build Health Analysis Command

Analyzes build pipeline health including performance metrics, reliability patterns, test efficiency, and artifact management.

## Usage

```bash
# Full build health analysis
claude run build_health

# Specific analysis types
claude run build_health --performance
claude run build_health --reliability
claude run build_health --tests
claude run build_health --artifacts

# Time-based analysis
claude run build_health --days 7
claude run build_health --since "2024-01-01"

# CI/CD specific analysis
claude run build_health --ci github-actions
claude run build_health --workflow "main.yml"
```

## Analysis Components

### 1. Build Performance Analysis

```bash
# Analyze build time trends
echo "=== BUILD PERFORMANCE ANALYSIS ==="

# Check if we're in a git repository
if [ -d .git ]; then
    # Analyze recent build times from CI logs
    echo "📊 Build Time Trends (Last 30 days):"

    # For GitHub Actions
    if [ -d .github/workflows ]; then
        echo "  Analyzing GitHub Actions build times..."
        # Note: Requires gh CLI to be installed
        if command -v gh &> /dev/null; then
            gh run list --limit 50 --json conclusion,createdAt,updatedAt,name | \
            jq -r '.[] |
                select(.conclusion == "success") |
                {
                    workflow: .name,
                    duration: ((.updatedAt | fromdate) - (.createdAt | fromdate)),
                    date: .createdAt
                } |
                "\(.date | split("T")[0]) - \(.workflow): \(.duration | floor)s"'
        fi
    fi

    # Local build time analysis
    echo -e "\n📈 Local Build Time Analysis:"

    # Python/FastAPI build times
    if [ -f "pyproject.toml" ] || [ -f "requirements.txt" ]; then
        echo "  Python Build Performance:"
        time_start=$(date +%s)
        pip install --dry-run -r requirements.txt &> /dev/null
        time_end=$(date +%s)
        echo "    Dependency resolution time: $((time_end - time_start))s"
    fi

    # React/TypeScript build times
    if [ -f "package.json" ]; then
        echo "  Frontend Build Performance:"
        if [ -f "yarn.lock" ]; then
            echo "    Using Yarn for package management"
            yarn list --depth=0 | wc -l | xargs echo "    Total dependencies:"
        elif [ -f "package-lock.json" ]; then
            echo "    Using NPM for package management"
            npm list --depth=0 2>/dev/null | wc -l | xargs echo "    Total dependencies:"
        fi
    fi

    # Docker build analysis
    if [ -f "Dockerfile" ]; then
        echo -e "\n🐳 Docker Build Analysis:"
        echo "    Analyzing Dockerfile efficiency..."
        grep -c "^RUN" Dockerfile | xargs echo "    Number of RUN commands:"
        grep -c "^COPY\|^ADD" Dockerfile | xargs echo "    Number of COPY/ADD commands:"
    fi
fi

# Incremental vs Full Build Analysis
echo -e "\n⚡ Build Type Analysis:"
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo "  Frontend incremental build support:"
    grep -q "webpack\|vite\|esbuild" frontend/package.json && echo "    ✅ Modern bundler detected"
    [ -d "frontend/.next" ] && echo "    ✅ Next.js incremental builds enabled"
fi

if [ -d "backend" ]; then
    echo "  Backend incremental build support:"
    [ -d "backend/__pycache__" ] && echo "    ✅ Python bytecode caching active"
    [ -d ".pytest_cache" ] && echo "    ✅ Pytest caching enabled"
fi

# Resource usage analysis
echo -e "\n💻 Resource Usage During Builds:"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "  Docker resource limits:"
    docker info 2>/dev/null | grep -E "CPUs:|Memory:" | sed 's/^/    /'
fi

# Parallel build efficiency
echo -e "\n🔄 Parallel Build Configuration:"
if [ -f "Makefile" ]; then
    grep -q "parallel\|jobs" Makefile && echo "  ✅ Makefile supports parallel builds"
fi
if [ -f "package.json" ]; then
    grep -q "concurrently\|npm-run-all" package.json && echo "  ✅ Frontend parallel tasks configured"
fi
```

### 2. Build Reliability Analysis

```bash
echo -e "\n=== BUILD RELIABILITY ANALYSIS ==="

# Failure pattern analysis
echo "🔍 Build Failure Patterns:"

# Check GitHub Actions failures
if command -v gh &> /dev/null && [ -d .github/workflows ]; then
    echo "  Recent failed builds:"
    gh run list --status failure --limit 10 --json conclusion,createdAt,name,event | \
    jq -r '.[] | "    \(.createdAt | split("T")[0]) - \(.name) (\(.event))"' | head -5

    echo -e "\n  Common failure reasons:"
    # Analyze workflow logs for common patterns
    gh run list --status failure --limit 20 --json databaseId | \
    jq -r '.[].databaseId' | while read run_id; do
        gh run view $run_id --log 2>/dev/null | grep -i "error\|failed" | head -1
    done | sort | uniq -c | sort -nr | head -5 | sed 's/^/    /'
fi

# Flaky test detection
echo -e "\n🎲 Flaky Test Detection:"
if [ -d ".pytest_cache" ]; then
    echo "  Python test flakiness:"
    find . -name "test_*.py" -o -name "*_test.py" | while read test_file; do
        grep -l "retry\|flaky\|skip\|xfail" "$test_file" 2>/dev/null && echo "    ⚠️  Potential flaky test: $test_file"
    done | head -5
fi

if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    echo "  Frontend test flakiness:"
    find frontend -name "*.test.js" -o -name "*.test.ts" -o -name "*.spec.js" -o -name "*.spec.ts" | while read test_file; do
        grep -l "skip\|todo\|setTimeout\|waitFor" "$test_file" 2>/dev/null && echo "    ⚠️  Potential flaky test: $test_file"
    done | head -5
fi

# Dependency resolution issues
echo -e "\n📦 Dependency Resolution Health:"
if [ -f "requirements.txt" ]; then
    echo "  Python dependencies:"
    # Check for conflicting versions
    grep -E "==|>=|<=" requirements.txt | wc -l | xargs echo "    Pinned dependencies:"
    grep -E "^[^#=<>]+$" requirements.txt | wc -l | xargs echo "    Unpinned dependencies:"
fi

if [ -f "package.json" ]; then
    echo "  JavaScript dependencies:"
    # Check for security vulnerabilities
    if command -v npm &> /dev/null; then
        npm audit --json 2>/dev/null | jq -r '.metadata | "    Vulnerabilities: \(.vulnerabilities.total) (High: \(.vulnerabilities.high), Critical: \(.vulnerabilities.critical))"' 2>/dev/null || echo "    Unable to check vulnerabilities"
    fi
fi

# Environment-specific failures
echo -e "\n🌍 Environment-Specific Issues:"
echo "  Checking for environment dependencies..."
grep -r "platform\|sys.platform\|os.name" --include="*.py" . 2>/dev/null | wc -l | xargs echo "    Platform-specific code instances:"
grep -r "process.env\|NODE_ENV" --include="*.js" --include="*.ts" . 2>/dev/null | wc -l | xargs echo "    Environment variable dependencies:"
```

### 3. Test Performance Analysis

```bash
echo -e "\n=== TEST PERFORMANCE ANALYSIS ==="

# Test execution time tracking
echo "⏱️  Test Execution Times:"

# Python test performance
if [ -f "pytest.ini" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
    echo "  Python Test Suite:"
    if [ -d ".pytest_cache" ]; then
        # Get test counts
        find . -name "test_*.py" -o -name "*_test.py" | wc -l | xargs echo "    Total test files:"
        grep -r "def test_" --include="*.py" . 2>/dev/null | wc -l | xargs echo "    Total test functions:"
    fi

    # Check for test parallelization
    grep -q "pytest-xdist\|pytest-parallel" requirements*.txt 2>/dev/null && echo "    ✅ Parallel test execution enabled"
fi

# Frontend test performance
if [ -f "frontend/package.json" ]; then
    echo -e "\n  Frontend Test Suite:"
    find frontend -name "*.test.*" -o -name "*.spec.*" | wc -l | xargs echo "    Total test files:"

    # Check test runner configuration
    grep -q "jest" frontend/package.json && echo "    ✅ Jest test runner configured"
    grep -q "vitest" frontend/package.json && echo "    ✅ Vitest test runner configured"

    # Check for parallel execution
    if [ -f "frontend/jest.config.js" ] || [ -f "frontend/jest.config.json" ]; then
        grep -q "maxWorkers" frontend/jest.config.* && echo "    ✅ Parallel test execution configured"
    fi
fi

# Coverage analysis performance
echo -e "\n📊 Coverage Report Generation:"
if [ -f ".coverage" ] || [ -d "htmlcov" ]; then
    echo "  Python coverage:"
    [ -f ".coverage" ] && ls -lh .coverage | awk '{print "    Coverage data size: " $5}'
    [ -d "htmlcov" ] && du -sh htmlcov | awk '{print "    HTML report size: " $1}'
fi

if [ -d "frontend/coverage" ]; then
    echo "  Frontend coverage:"
    du -sh frontend/coverage | awk '{print "    Coverage report size: " $1}'
fi

# Test organization analysis
echo -e "\n🗂️  Test Organization:"
echo "  Test structure analysis:"

# Check for test organization patterns
test_patterns=(
    "unit"
    "integration"
    "e2e"
    "functional"
    "performance"
)

for pattern in "${test_patterns[@]}"; do
    count=$(find . -type d -name "*${pattern}*" | grep -E "test|spec" | wc -l)
    [ $count -gt 0 ] && echo "    ${pattern^} test directories: $count"
done
```

### 4. Artifact Management Analysis

```bash
echo -e "\n=== ARTIFACT MANAGEMENT ANALYSIS ==="

# Docker image size tracking
echo "🐳 Docker Image Analysis:"
if command -v docker &> /dev/null && [ -f "Dockerfile" ]; then
    echo "  Local Docker images:"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "mobius|context-engine" | head -5 | sed 's/^/    /'

    # Analyze Dockerfile for optimization opportunities
    echo -e "\n  Dockerfile optimization opportunities:"

    # Check for multi-stage builds
    grep -q "FROM.*AS" Dockerfile && echo "    ✅ Multi-stage build detected" || echo "    ⚠️  Consider using multi-stage builds"

    # Check for layer caching optimization
    grep -q "COPY requirements.*\nRUN pip install" Dockerfile && echo "    ✅ Dependency layer caching optimized"

    # Check for .dockerignore
    [ -f ".dockerignore" ] && echo "    ✅ .dockerignore file present" || echo "    ⚠️  Missing .dockerignore file"
fi

# Build artifact size trends
echo -e "\n📦 Build Artifact Sizes:"

# Python artifacts
if [ -d "dist" ]; then
    echo "  Python distribution artifacts:"
    ls -lh dist/*.whl dist/*.tar.gz 2>/dev/null | awk '{print "    " $9 ": " $5}' | tail -5
fi

# Frontend build artifacts
if [ -d "frontend/build" ] || [ -d "frontend/dist" ] || [ -d "frontend/.next" ]; then
    echo "  Frontend build artifacts:"
    for dir in frontend/build frontend/dist frontend/.next; do
        [ -d "$dir" ] && du -sh "$dir" | awk '{print "    " $2 ": " $1}'
    done
fi

# Dependency cache effectiveness
echo -e "\n💾 Cache Effectiveness:"

# Python cache
if [ -d ".pip-cache" ] || [ -d "~/.cache/pip" ]; then
    echo "  Python dependency cache:"
    cache_dir="${HOME}/.cache/pip"
    [ -d "$cache_dir" ] && du -sh "$cache_dir" 2>/dev/null | awk '{print "    Cache size: " $1}'
fi

# Node modules cache
if [ -d "node_modules" ]; then
    echo "  Node modules analysis:"
    du -sh node_modules | awk '{print "    Total size: " $1}'
    find node_modules -maxdepth 1 -type d | wc -l | xargs echo "    Direct dependencies:"
fi

# Package size analysis
echo -e "\n📏 Package Size Analysis:"

# Analyze Python package sizes
if [ -f "requirements.txt" ]; then
    echo "  Largest Python dependencies:"
    if command -v pip &> /dev/null; then
        pip list --format=json 2>/dev/null | \
        jq -r '.[] | .name' | \
        xargs -I {} sh -c 'size=$(pip show {} 2>/dev/null | grep -E "Location:|Size:" | tail -1); echo "{}: $size"' | \
        grep -v ": $" | sort -k2 -hr | head -5 | sed 's/^/    /'
    fi
fi

# Frontend bundle analysis
if [ -f "frontend/package.json" ]; then
    echo -e "\n  Frontend bundle analysis:"
    # Check for bundle analyzer
    grep -q "webpack-bundle-analyzer\|rollup-plugin-visualizer" frontend/package.json && \
        echo "    ✅ Bundle analyzer configured" || \
        echo "    ⚠️  Consider adding bundle analyzer"
fi
```

### 5. CI/CD Pipeline Analysis

```bash
echo -e "\n=== CI/CD PIPELINE ANALYSIS ==="

# GitHub Actions analysis
if [ -d ".github/workflows" ]; then
    echo "🔄 GitHub Actions Configuration:"
    echo "  Workflow files:"
    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        [ -f "$workflow" ] && echo "    - $(basename $workflow)"
    done

    echo -e "\n  Workflow efficiency analysis:"

    # Check for caching
    grep -l "actions/cache\|cache:" .github/workflows/*.y*ml 2>/dev/null | wc -l | \
        xargs echo "    Workflows using caching:"

    # Check for matrix builds
    grep -l "matrix:" .github/workflows/*.y*ml 2>/dev/null | wc -l | \
        xargs echo "    Workflows using matrix builds:"

    # Check for artifact uploads
    grep -l "actions/upload-artifact\|actions/download-artifact" .github/workflows/*.y*ml 2>/dev/null | wc -l | \
        xargs echo "    Workflows using artifacts:"

    # Analyze workflow triggers
    echo -e "\n  Workflow triggers:"
    grep -h "on:" -A 5 .github/workflows/*.y*ml 2>/dev/null | \
        grep -E "push:|pull_request:|schedule:|workflow_dispatch:" | \
        sort | uniq -c | sed 's/^/    /'
fi

# Performance metrics from CI
if command -v gh &> /dev/null; then
    echo -e "\n📈 CI Performance Metrics (Last 7 days):"

    # Get average build times by workflow
    echo "  Average build times:"
    gh run list --limit 50 --json workflowName,createdAt,updatedAt,conclusion | \
    jq -r '
        group_by(.workflowName) |
        map({
            workflow: .[0].workflowName,
            avg_duration: (map(select(.conclusion == "success") | ((.updatedAt | fromdate) - (.createdAt | fromdate))) | add / length | floor),
            success_rate: ((map(select(.conclusion == "success")) | length) / length * 100 | floor)
        }) |
        .[] | "    \(.workflow): \(.avg_duration)s (Success: \(.success_rate)%)"'
fi
```

### 6. Summary Report

```bash
echo -e "\n=== BUILD HEALTH SUMMARY ==="

# Overall health score calculation
health_score=100
warnings=0

# Check various health indicators
[ ! -f ".dockerignore" ] && ((health_score-=5)) && ((warnings++))
[ ! -d ".github/workflows" ] && ((health_score-=10)) && ((warnings++))
grep -q "test" Makefile 2>/dev/null || grep -q "test" package.json 2>/dev/null || ((health_score-=10)) && ((warnings++))

# Docker checks
if [ -f "Dockerfile" ]; then
    grep -q "FROM.*AS" Dockerfile || ((health_score-=5)) && ((warnings++))
fi

# Dependency health
if [ -f "requirements.txt" ]; then
    unpinned=$(grep -E "^[^#=<>]+$" requirements.txt | wc -l)
    [ $unpinned -gt 5 ] && ((health_score-=10)) && ((warnings++))
fi

echo "📊 Overall Build Health Score: ${health_score}/100"
echo "⚠️  Total warnings found: $warnings"

echo -e "\n🎯 Key Recommendations:"
[ ! -f ".dockerignore" ] && echo "  • Add .dockerignore file to optimize Docker builds"
[ ! -d ".github/workflows" ] && echo "  • Set up CI/CD with GitHub Actions"
grep -q "FROM.*AS" Dockerfile 2>/dev/null || echo "  • Use multi-stage Docker builds to reduce image size"
[ $unpinned -gt 5 ] 2>/dev/null && echo "  • Pin more dependencies for reproducible builds"

echo -e "\n📋 Next Steps:"
echo "  1. Address critical warnings first"
echo "  2. Implement caching strategies for faster builds"
echo "  3. Add build performance monitoring"
echo "  4. Regular dependency updates and security audits"
```

## Error Handling

```bash
# Handle missing tools gracefully
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "⚠️  Warning: $1 is not installed. Some features may be limited."
        return 1
    fi
    return 0
}

# Check required tools
check_tool git
check_tool docker
check_tool gh
check_tool jq
```

## Integration with Mobius

This command integrates with the Mobius platform by:

1. **Performance Tracking**: Monitors build times to ensure <200ms latency targets
2. **Multi-Region Support**: Analyzes build artifacts for different deployment regions
3. **Container Optimization**: Ensures Docker images are optimized for Kubernetes deployment
4. **Test Coverage**: Validates comprehensive test coverage for all components
5. **CI/CD Health**: Monitors GitHub Actions workflows for the platform

## Advanced Options

```bash
# Generate detailed reports
claude run build_health --format json > build-health-report.json
claude run build_health --format html > build-health-report.html

# Compare with baseline
claude run build_health --baseline "last-week"
claude run build_health --compare "main"

# Export metrics
claude run build_health --export-metrics prometheus
claude run build_health --export-metrics datadog
```
