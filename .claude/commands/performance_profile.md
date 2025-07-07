# Performance Profile Analysis

Comprehensive performance profiling and analysis for the Mobius platform, covering backend (FastAPI/Python), frontend (React/TypeScript), database operations, and system-level performance.

## Command

```bash
# Full stack performance profile
python scripts/performance_profile.py --mode full --output reports/performance_$(date +%Y%m%d_%H%M%S).json

# Backend-specific profiling
python scripts/performance_profile.py --mode backend --endpoints all --duration 60

# Frontend-specific profiling
npm run profile:frontend -- --lighthouse --bundle-analyze

# Database performance analysis
python scripts/performance_profile.py --mode database --queries analyze

# System resource profiling
python scripts/performance_profile.py --mode system --containers all
```

## Parameters

- `--mode`: Profiling mode: full, backend, frontend, database, system (default: full)
- `--output`: Output file for performance report (default: stdout)
- `--format`: Output format: json, html, markdown, flamegraph (default: json)
- `--duration`: Duration for profiling in seconds (default: 60)
- `--endpoints`: API endpoints to profile: all, specific paths (default: critical)
- `--load`: Simulated load level: light, normal, heavy (default: normal)
- `--profile-type`: Backend profiler: cprofile, py-spy, memory, async (default: cprofile)
- `--containers`: Container names to profile (default: all)
- `--baseline`: Compare against baseline performance file

## Backend Performance Profiling

### CPU Profiling

```bash
# cProfile for detailed function-level profiling
python -m cProfile -o backend.prof backend/main.py
python -m pstats backend.prof

# py-spy for production profiling without overhead
py-spy record -d 60 -o profile.svg -- python backend/main.py
py-spy top -- python backend/main.py

# Line profiler for specific functions
kernprof -l -v backend/api/endpoints/context.py
```

### Memory Profiling

```bash
# Memory profiler with decorators
python -m memory_profiler backend/main.py

# Tracemalloc for memory allocation tracking
python scripts/memory_trace.py --module backend.main --top 25

# Fil memory profiler for memory usage over time
fil-profile run backend/main.py
```

### Async Performance

```bash
# AsyncIO profiling
python scripts/async_profile.py --inspect-tasks --measure-latency

# aiomonitor for live async inspection
python -m aiomonitor backend/main.py
```

### API Endpoint Analysis

```bash
# FastAPI route profiling
python scripts/api_profile.py \
  --endpoints "/api/context/*,/api/agents/*" \
  --requests 1000 \
  --concurrent 50 \
  --measure "latency,throughput,errors"
```

## Frontend Performance Profiling

### Bundle Analysis

```bash
# Webpack bundle analyzer
npm run build -- --stats
npx webpack-bundle-analyzer dist/stats.json

# Source map explorer
npm run build:sourcemap
npx source-map-explorer 'dist/*.js'

# Bundle size tracking
npx bundlesize --config .bundlesizerc.json
```

### React Performance

```bash
# React DevTools Profiler export
npm run profile:react -- --record 60 --export profile.json

# React component render analysis
npx why-did-you-render

# Component performance monitoring
npm run test:performance -- --coverage
```

### Core Web Vitals

```bash
# Lighthouse CI
npx lighthouse http://localhost:3000 \
  --output json \
  --output-path ./lighthouse-report.json \
  --chrome-flags="--headless"

# Web Vitals monitoring
npm run vitals:measure -- --url http://localhost:3000 --iterations 10
```

### Network Performance

```bash
# Network waterfall analysis
npx chrome-har-capturer -o network.har http://localhost:3000

# Resource timing analysis
node scripts/resource_timing.js --url http://localhost:3000
```

## Database Performance

### PostgreSQL Profiling

```sql
-- Enable query timing
ALTER DATABASE mobius SET log_min_duration_statement = 100;

-- Query performance analysis
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM contexts 
WHERE workspace_id = '123' 
AND created_at > NOW() - INTERVAL '7 days';

-- Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Vector Database Performance

```python
# Qdrant performance testing
python scripts/vector_db_profile.py \
  --operation "search,insert,update" \
  --vectors 10000 \
  --dimensions 1536 \
  --batch-size 100

# Pinecone performance comparison
python scripts/vector_db_benchmark.py \
  --providers "qdrant,pinecone" \
  --dataset "embeddings_test.npy"
```

### Redis Cache Analysis

```bash
# Redis performance benchmarking
redis-benchmark -h localhost -p 6379 -c 50 -n 10000

# Cache hit rate analysis
redis-cli --stat

# Memory usage profiling
redis-cli --bigkeys
redis-cli memory stats
```

### Connection Pool Monitoring

```python
# Database connection pool metrics
python scripts/db_pool_monitor.py \
  --pools "postgres,redis,qdrant" \
  --metrics "active,idle,wait_time" \
  --interval 5
```

## System Performance

### Container Resource Usage

```bash
# Docker stats monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Container profiling with cAdvisor
docker run -d \
  --volume=/var/run/docker.sock:/var/run/docker.sock:ro \
  --publish=8080:8080 \
  google/cadvisor:latest

# Kubernetes pod metrics
kubectl top pods -n mobius --containers
kubectl describe pod <pod-name> -n mobius
```

### Memory Leak Detection

```bash
# Python memory leak detection
python -m tracemalloc backend/main.py
python scripts/memory_leak_detector.py --threshold 100MB --duration 3600

# Node.js memory leak detection
node --inspect --max-old-space-size=4096 frontend/server.js
node scripts/heap_snapshot.js --interval 300 --count 12
```

### CPU Bottleneck Analysis

```bash
# System-wide CPU profiling
perf record -F 99 -p $(pgrep python) -- sleep 60
perf report

# Python specific CPU profiling
py-spy record -d 60 -f speedscope -o cpu_profile.json -- python backend/main.py

# Node.js CPU profiling
node --cpu-prof frontend/server.js
node --prof-process isolate-*.log > processed.txt
```

### I/O Performance

```bash
# Disk I/O monitoring
iotop -o -b -d 2 -n 30 > io_report.txt

# Network I/O analysis
iftop -t -s 60 > network_io.txt

# File system operations tracing
strace -c -f -e trace=file python backend/main.py
```

## Performance Testing Scripts

### Load Testing

```python
# scripts/load_test.py
import asyncio
import aiohttp
import time
from statistics import mean, stdev

async def load_test_endpoint(session, url, payload):
    start = time.time()
    async with session.post(url, json=payload) as response:
        await response.text()
        return time.time() - start

async def run_load_test(endpoint, concurrent_users, requests_per_user):
    url = f"http://localhost:8000{endpoint}"
    payload = {"workspace_id": "test", "content": "test content"}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(requests_per_user):
                tasks.append(load_test_endpoint(session, url, payload))
        
        results = await asyncio.gather(*tasks)
        
    return {
        "endpoint": endpoint,
        "total_requests": len(results),
        "avg_response_time": mean(results),
        "std_dev": stdev(results),
        "min_time": min(results),
        "max_time": max(results),
        "requests_per_second": len(results) / sum(results)
    }
```

### Memory Profiling

```python
# scripts/memory_profile.py
import tracemalloc
import psutil
import gc
import time

class MemoryProfiler:
    def __init__(self, threshold_mb=100):
        self.threshold_mb = threshold_mb
        self.baseline = None
        tracemalloc.start()
        
    def take_snapshot(self):
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        total_mb = sum(stat.size for stat in top_stats) / 1024 / 1024
        
        return {
            "timestamp": time.time(),
            "total_mb": total_mb,
            "top_allocations": [
                {
                    "file": stat.traceback.format()[0],
                    "size_mb": stat.size / 1024 / 1024,
                    "count": stat.count
                }
                for stat in top_stats[:10]
            ],
            "process_memory": {
                "rss_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "vms_mb": psutil.Process().memory_info().vms / 1024 / 1024,
                "percent": psutil.Process().memory_percent()
            }
        }
    
    def detect_leak(self, duration_seconds=3600, interval_seconds=60):
        snapshots = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            snapshot = self.take_snapshot()
            snapshots.append(snapshot)
            
            if len(snapshots) > 1:
                growth = snapshot["total_mb"] - snapshots[0]["total_mb"]
                if growth > self.threshold_mb:
                    return {
                        "leak_detected": True,
                        "growth_mb": growth,
                        "duration_seconds": time.time() - start_time,
                        "snapshots": snapshots
                    }
            
            gc.collect()
            time.sleep(interval_seconds)
        
        return {
            "leak_detected": False,
            "snapshots": snapshots
        }
```

### Async Performance Monitor

```python
# scripts/async_monitor.py
import asyncio
import time
from collections import defaultdict

class AsyncPerformanceMonitor:
    def __init__(self):
        self.task_times = defaultdict(list)
        self.active_tasks = {}
        
    def monitor_task(self, coro, name=None):
        async def wrapped():
            task_id = id(asyncio.current_task())
            name_key = name or coro.__name__
            
            start_time = time.time()
            self.active_tasks[task_id] = {
                "name": name_key,
                "start": start_time
            }
            
            try:
                result = await coro
                duration = time.time() - start_time
                self.task_times[name_key].append(duration)
                return result
            finally:
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
        
        return wrapped()
    
    def get_stats(self):
        stats = {}
        for task_name, times in self.task_times.items():
            if times:
                stats[task_name] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "avg_time": mean(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        return stats
    
    def get_active_tasks(self):
        current_time = time.time()
        return [
            {
                "name": info["name"],
                "duration": current_time - info["start"]
            }
            for info in self.active_tasks.values()
        ]
```

## Performance Benchmarks

### Target Metrics

```yaml
# performance_targets.yaml
api_endpoints:
  context_create:
    p50_latency: 100ms
    p95_latency: 200ms
    p99_latency: 500ms
    throughput: 1000 req/s
  
  context_search:
    p50_latency: 50ms
    p95_latency: 150ms
    p99_latency: 300ms
    throughput: 5000 req/s

frontend:
  first_contentful_paint: 1.8s
  time_to_interactive: 3.5s
  cumulative_layout_shift: 0.1
  bundle_size: 500KB
  
database:
  query_response_time: 10ms
  connection_pool_size: 100
  cache_hit_rate: 90%
  
system:
  cpu_usage: <70%
  memory_usage: <80%
  container_startup: <30s
```

## Continuous Performance Monitoring

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Mobius Performance Dashboard",
    "panels": [
      {
        "title": "API Response Times",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)",
            "legendFormat": "p95 latency"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "process_resident_memory_bytes / 1024 / 1024",
            "legendFormat": "RSS (MB)"
          }
        ]
      },
      {
        "title": "Database Performance",
        "targets": [
          {
            "expr": "pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)",
            "legendFormat": "Cache hit ratio"
          }
        ]
      }
    ]
  }
}
```

### Performance CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily performance regression test

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Environment
        run: |
          docker-compose up -d
          pip install -r requirements-dev.txt
          npm ci
      
      - name: Run Performance Tests
        run: |
          python scripts/performance_profile.py \
            --mode full \
            --output performance_report.json \
            --baseline baseline_performance.json
      
      - name: Check Performance Regression
        run: |
          python scripts/check_performance_regression.py \
            --current performance_report.json \
            --baseline baseline_performance.json \
            --threshold 10
      
      - name: Upload Performance Report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: performance_report.json
```

## Optimization Workflow

1. **Profile First**: Always measure before optimizing
2. **Identify Bottlenecks**: Focus on the slowest parts (80/20 rule)
3. **Benchmark Changes**: Compare before and after metrics
4. **Monitor Production**: Continuous performance tracking
5. **Set Alerts**: Automated alerts for performance degradation

## Troubleshooting

### Common Performance Issues

1. **High API Latency**
   - Check database query performance
   - Review async operation efficiency
   - Analyze serialization overhead

2. **Memory Leaks**
   - Use memory profilers to identify growth
   - Check for circular references
   - Review cache eviction policies

3. **Frontend Performance**
   - Analyze bundle size and code splitting
   - Check for unnecessary re-renders
   - Review network request waterfall

4. **Database Bottlenecks**
   - Analyze slow query logs
   - Check index usage
   - Review connection pool settings

### Debug Commands

```bash
# Quick performance check
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/health

# Python GC stats
python -c "import gc; gc.set_debug(gc.DEBUG_STATS); exec(open('backend/main.py').read())"

# Node.js heap snapshot
node --inspect --heap-prof frontend/server.js
chrome://inspect

# Database locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

## Best Practices

1. **Establish Baselines**: Record performance metrics before changes
2. **Profile Regularly**: Weekly performance profiling in development
3. **Production Monitoring**: Real-time performance dashboards
4. **Performance Budget**: Set and enforce performance budgets
5. **Incremental Optimization**: Small, measurable improvements