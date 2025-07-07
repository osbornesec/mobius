# API Health Monitoring Command

Monitor and analyze the health of Mobius FastAPI backend endpoints with comprehensive metrics.

## Prerequisites

```bash
pip install httpx pytest-asyncio prometheus-client pydantic fastapi[all] sqlalchemy redis aioredis psutil matplotlib pandas tabulate rich click
```

## Command Usage

```bash
# Full API health check
python scripts/api_health.py --full-scan

# Monitor specific endpoint
python scripts/api_health.py --endpoint /api/v1/contexts --duration 60

# Generate health report
python scripts/api_health.py --report --output reports/api_health_$(date +%Y%m%d).html

# Real-time monitoring dashboard
python scripts/api_health.py --dashboard

# Performance stress test
python scripts/api_health.py --stress-test --concurrent 100 --duration 300
```

## Core Script

Create the main monitoring script:

```python
#!/usr/bin/env python3
"""
API Health Monitoring Tool for Mobius Platform
Monitors endpoint health, performance, and compliance.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

import httpx
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import pandas as pd
from pydantic import BaseModel, ValidationError
from fastapi.testclient import TestClient
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import psutil
import aioredis
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from tabulate import tabulate

console = Console()

# Metrics collectors
request_count = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint', 'method'])
active_connections = Gauge('api_active_connections', 'Active API connections')
error_rate = Gauge('api_error_rate', 'API error rate percentage', ['endpoint'])
cache_hit_rate = Gauge('api_cache_hit_rate', 'Cache hit rate percentage')

@dataclass
class EndpointMetrics:
    """Metrics for a single endpoint."""
    endpoint: str
    method: str = "GET"
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    error_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    request_sizes: List[int] = field(default_factory=list)
    response_sizes: List[int] = field(default_factory=list)
    cache_hits: int = 0
    cache_misses: int = 0
    db_query_times: List[float] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
    
    @property
    def cache_hit_rate(self) -> float:
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100


class APIHealthMonitor:
    """Main API health monitoring class."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.metrics: Dict[str, EndpointMetrics] = {}
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.openapi_spec = None
        self.redis_client = None
        self.db_engine = None
        
    async def initialize(self):
        """Initialize connections and load OpenAPI spec."""
        try:
            # Load OpenAPI specification
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/openapi.json")
                if response.status_code == 200:
                    self.openapi_spec = response.json()
                    console.print("[green]✓ Loaded OpenAPI specification[/green]")
                else:
                    console.print("[yellow]⚠ Could not load OpenAPI spec[/yellow]")
            
            # Initialize Redis connection
            try:
                self.redis_client = await aioredis.create_redis_pool('redis://localhost')
                console.print("[green]✓ Connected to Redis[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Redis connection failed: {e}[/yellow]")
            
            # Initialize database connection
            try:
                self.db_engine = create_engine("postgresql://user:password@localhost/mobius")
                console.print("[green]✓ Connected to PostgreSQL[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Database connection failed: {e}[/yellow]")
                
        except Exception as e:
            console.print(f"[red]✗ Initialization error: {e}[/red]")
    
    async def test_endpoint(self, endpoint: str, method: str = "GET", 
                          payload: Optional[Dict] = None) -> EndpointMetrics:
        """Test a single endpoint and collect metrics."""
        metrics = self.metrics.get(f"{method}:{endpoint}", 
                                 EndpointMetrics(endpoint=endpoint, method=method))
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            try:
                # Prepare request
                kwargs = {"headers": self.headers}
                if payload:
                    kwargs["json"] = payload
                
                # Make request
                response = await client.request(
                    method, 
                    f"{self.base_url}{endpoint}",
                    **kwargs
                )
                
                # Calculate metrics
                response_time = time.time() - start_time
                metrics.response_times.append(response_time)
                metrics.total_requests += 1
                
                if 200 <= response.status_code < 300:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                    metrics.error_codes[response.status_code] += 1
                
                # Size metrics
                request_size = len(json.dumps(payload) if payload else "")
                response_size = len(response.content)
                metrics.request_sizes.append(request_size)
                metrics.response_sizes.append(response_size)
                
                # Check cache headers
                if "X-Cache-Hit" in response.headers:
                    if response.headers["X-Cache-Hit"] == "true":
                        metrics.cache_hits += 1
                    else:
                        metrics.cache_misses += 1
                
                # Update Prometheus metrics
                request_count.labels(endpoint=endpoint, method=method, 
                                   status=response.status_code).inc()
                request_duration.labels(endpoint=endpoint, method=method).observe(response_time)
                
            except Exception as e:
                metrics.failed_requests += 1
                metrics.total_requests += 1
                console.print(f"[red]✗ Error testing {endpoint}: {e}[/red]")
        
        self.metrics[f"{method}:{endpoint}"] = metrics
        return metrics
    
    async def run_full_scan(self):
        """Scan all endpoints from OpenAPI spec."""
        if not self.openapi_spec:
            console.print("[red]✗ No OpenAPI spec available[/red]")
            return
        
        endpoints = []
        for path, methods in self.openapi_spec.get("paths", {}).items():
            for method in methods:
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append((path, method.upper()))
        
        console.print(f"[cyan]Scanning {len(endpoints)} endpoints...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Testing endpoints...", total=len(endpoints))
            
            for endpoint, method in endpoints:
                await self.test_endpoint(endpoint, method)
                progress.update(task, advance=1, 
                              description=f"Testing {method} {endpoint}")
    
    async def monitor_endpoint_live(self, endpoint: str, duration: int = 60):
        """Monitor an endpoint in real-time."""
        console.print(f"[cyan]Monitoring {endpoint} for {duration} seconds...[/cyan]")
        
        start_time = time.time()
        
        with Live(self._generate_live_table(endpoint), refresh_per_second=1) as live:
            while time.time() - start_time < duration:
                await self.test_endpoint(endpoint)
                live.update(self._generate_live_table(endpoint))
                await asyncio.sleep(1)
    
    def _generate_live_table(self, endpoint: str) -> Table:
        """Generate a live monitoring table."""
        metrics = self.metrics.get(f"GET:{endpoint}", EndpointMetrics(endpoint=endpoint))
        
        table = Table(title=f"Live Monitoring: {endpoint}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Requests", str(metrics.total_requests))
        table.add_row("Success Rate", f"{metrics.success_rate:.2f}%")
        table.add_row("Avg Response Time", f"{metrics.avg_response_time:.3f}s")
        table.add_row("P95 Response Time", f"{metrics.p95_response_time:.3f}s")
        table.add_row("Cache Hit Rate", f"{metrics.cache_hit_rate:.2f}%")
        table.add_row("Active Connections", str(active_connections._value.get()))
        
        return table
    
    async def stress_test(self, endpoint: str, concurrent: int = 100, 
                         duration: int = 60):
        """Run stress test on endpoint."""
        console.print(f"[cyan]Stress testing {endpoint} with {concurrent} concurrent requests for {duration}s...[/cyan]")
        
        async def worker():
            while time.time() - start_time < duration:
                await self.test_endpoint(endpoint)
        
        start_time = time.time()
        tasks = [asyncio.create_task(worker()) for _ in range(concurrent)]
        await asyncio.gather(*tasks)
        
        metrics = self.metrics.get(f"GET:{endpoint}")
        if metrics:
            console.print(f"[green]✓ Completed {metrics.total_requests} requests[/green]")
            console.print(f"[yellow]Success rate: {metrics.success_rate:.2f}%[/yellow]")
            console.print(f"[yellow]Avg response time: {metrics.avg_response_time:.3f}s[/yellow]")
    
    def validate_api_standards(self) -> List[Dict]:
        """Validate API against REST standards and best practices."""
        issues = []
        
        if not self.openapi_spec:
            return [{"severity": "critical", "issue": "No OpenAPI specification found"}]
        
        paths = self.openapi_spec.get("paths", {})
        
        # Check RESTful naming conventions
        for path in paths:
            if not path.startswith("/api/v"):
                issues.append({
                    "severity": "warning",
                    "issue": f"Path '{path}' does not follow versioning convention"
                })
            
            # Check for proper resource naming
            parts = path.split("/")
            for i, part in enumerate(parts):
                if part and not (part.startswith("{") or part.startswith("v") or part == "api"):
                    if part != part.lower():
                        issues.append({
                            "severity": "warning",
                            "issue": f"Resource '{part}' in path '{path}' should be lowercase"
                        })
        
        # Check for consistent error responses
        for path, methods in paths.items():
            for method, details in methods.items():
                responses = details.get("responses", {})
                
                # Should have standard error responses
                if "400" not in responses:
                    issues.append({
                        "severity": "info",
                        "issue": f"{method.upper()} {path} missing 400 Bad Request response"
                    })
                
                if method.upper() in ["POST", "PUT", "PATCH", "DELETE"] and "401" not in responses:
                    issues.append({
                        "severity": "warning",
                        "issue": f"{method.upper()} {path} missing 401 Unauthorized response"
                    })
        
        # Check for rate limiting headers
        sample_endpoint = list(paths.keys())[0] if paths else None
        if sample_endpoint:
            metrics = self.metrics.get(f"GET:{sample_endpoint}")
            if metrics and metrics.total_requests > 0:
                # Check if rate limit headers are present
                # This would need actual response header checking
                pass
        
        return issues
    
    def generate_report(self, output_format: str = "html") -> str:
        """Generate comprehensive health report."""
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "endpoints_tested": len(self.metrics),
            "total_requests": sum(m.total_requests for m in self.metrics.values()),
            "overall_success_rate": self._calculate_overall_success_rate(),
            "endpoint_metrics": [],
            "api_standards": self.validate_api_standards(),
            "performance_summary": self._generate_performance_summary()
        }
        
        # Compile endpoint metrics
        for key, metrics in self.metrics.items():
            report_data["endpoint_metrics"].append({
                "endpoint": metrics.endpoint,
                "method": metrics.method,
                "total_requests": metrics.total_requests,
                "success_rate": metrics.success_rate,
                "avg_response_time": metrics.avg_response_time,
                "p95_response_time": metrics.p95_response_time,
                "cache_hit_rate": metrics.cache_hit_rate,
                "error_codes": dict(metrics.error_codes)
            })
        
        if output_format == "html":
            return self._generate_html_report(report_data)
        elif output_format == "json":
            return json.dumps(report_data, indent=2)
        else:
            return self._generate_text_report(report_data)
    
    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall API success rate."""
        total_requests = sum(m.total_requests for m in self.metrics.values())
        successful_requests = sum(m.successful_requests for m in self.metrics.values())
        
        if total_requests == 0:
            return 0.0
        return (successful_requests / total_requests) * 100
    
    def _generate_performance_summary(self) -> Dict:
        """Generate performance summary statistics."""
        all_response_times = []
        for metrics in self.metrics.values():
            all_response_times.extend(metrics.response_times)
        
        if not all_response_times:
            return {}
        
        return {
            "avg_response_time": statistics.mean(all_response_times),
            "median_response_time": statistics.median(all_response_times),
            "p95_response_time": sorted(all_response_times)[int(len(all_response_times) * 0.95)],
            "p99_response_time": sorted(all_response_times)[int(len(all_response_times) * 0.99)],
            "min_response_time": min(all_response_times),
            "max_response_time": max(all_response_times)
        }
    
    def _generate_html_report(self, data: Dict) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mobius API Health Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metric-card {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .danger {{ color: #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mobius API Health Report</h1>
                <p>Generated: {data['timestamp']}</p>
                <p>Base URL: {data['base_url']}</p>
            </div>
            
            <div class="metric-card">
                <h2>Overall Metrics</h2>
                <p>Endpoints Tested: {data['endpoints_tested']}</p>
                <p>Total Requests: {data['total_requests']}</p>
                <p class="{'success' if data['overall_success_rate'] > 95 else 'warning' if data['overall_success_rate'] > 90 else 'danger'}">
                    Overall Success Rate: {data['overall_success_rate']:.2f}%
                </p>
            </div>
            
            <h2>Endpoint Performance</h2>
            <table>
                <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Requests</th>
                    <th>Success Rate</th>
                    <th>Avg Response Time</th>
                    <th>P95 Response Time</th>
                    <th>Cache Hit Rate</th>
                </tr>
        """
        
        for endpoint in data['endpoint_metrics']:
            success_class = 'success' if endpoint['success_rate'] > 95 else 'warning' if endpoint['success_rate'] > 90 else 'danger'
            html += f"""
                <tr>
                    <td>{endpoint['endpoint']}</td>
                    <td>{endpoint['method']}</td>
                    <td>{endpoint['total_requests']}</td>
                    <td class="{success_class}">{endpoint['success_rate']:.2f}%</td>
                    <td>{endpoint['avg_response_time']:.3f}s</td>
                    <td>{endpoint['p95_response_time']:.3f}s</td>
                    <td>{endpoint['cache_hit_rate']:.2f}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h2>API Standards Compliance</h2>
            <div class="metric-card">
        """
        
        if data['api_standards']:
            html += "<ul>"
            for issue in data['api_standards']:
                severity_class = 'danger' if issue['severity'] == 'critical' else 'warning' if issue['severity'] == 'warning' else ''
                html += f'<li class="{severity_class}">[{issue["severity"].upper()}] {issue["issue"]}</li>'
            html += "</ul>"
        else:
            html += '<p class="success">All API standards checks passed!</p>'
        
        html += """
            </div>
            
            <h2>Performance Summary</h2>
            <div class="metric-card">
        """
        
        if data['performance_summary']:
            perf = data['performance_summary']
            html += f"""
                <p>Average Response Time: {perf['avg_response_time']:.3f}s</p>
                <p>Median Response Time: {perf['median_response_time']:.3f}s</p>
                <p>95th Percentile: {perf['p95_response_time']:.3f}s</p>
                <p>99th Percentile: {perf['p99_response_time']:.3f}s</p>
                <p>Min Response Time: {perf['min_response_time']:.3f}s</p>
                <p>Max Response Time: {perf['max_response_time']:.3f}s</p>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_report(self, data: Dict) -> str:
        """Generate text report."""
        report = f"""
MOBIUS API HEALTH REPORT
========================
Generated: {data['timestamp']}
Base URL: {data['base_url']}

OVERALL METRICS
--------------
Endpoints Tested: {data['endpoints_tested']}
Total Requests: {data['total_requests']}
Overall Success Rate: {data['overall_success_rate']:.2f}%

ENDPOINT PERFORMANCE
-------------------
"""
        
        # Create table data
        headers = ["Endpoint", "Method", "Requests", "Success Rate", "Avg Response", "P95 Response", "Cache Hit Rate"]
        rows = []
        
        for endpoint in data['endpoint_metrics']:
            rows.append([
                endpoint['endpoint'],
                endpoint['method'],
                endpoint['total_requests'],
                f"{endpoint['success_rate']:.2f}%",
                f"{endpoint['avg_response_time']:.3f}s",
                f"{endpoint['p95_response_time']:.3f}s",
                f"{endpoint['cache_hit_rate']:.2f}%"
            ])
        
        report += tabulate(rows, headers=headers, tablefmt="grid")
        
        report += "\n\nAPI STANDARDS COMPLIANCE\n------------------------\n"
        
        if data['api_standards']:
            for issue in data['api_standards']:
                report += f"[{issue['severity'].upper()}] {issue['issue']}\n"
        else:
            report += "All API standards checks passed!\n"
        
        if data['performance_summary']:
            perf = data['performance_summary']
            report += f"""
PERFORMANCE SUMMARY
------------------
Average Response Time: {perf['avg_response_time']:.3f}s
Median Response Time: {perf['median_response_time']:.3f}s
95th Percentile: {perf['p95_response_time']:.3f}s
99th Percentile: {perf['p99_response_time']:.3f}s
Min Response Time: {perf['min_response_time']:.3f}s
Max Response Time: {perf['max_response_time']:.3f}s
"""
        
        return report
    
    async def check_database_performance(self):
        """Check database query performance for API endpoints."""
        if not self.db_engine:
            console.print("[yellow]⚠ Database connection not available[/yellow]")
            return
        
        # Sample queries to test
        test_queries = [
            ("SELECT COUNT(*) FROM contexts", "Count contexts"),
            ("SELECT * FROM contexts LIMIT 100", "Fetch contexts"),
            ("SELECT * FROM users WHERE id = 1", "Fetch user by ID"),
        ]
        
        results = []
        
        with self.db_engine.connect() as conn:
            for query, description in test_queries:
                start_time = time.time()
                try:
                    conn.execute(text(query))
                    duration = time.time() - start_time
                    results.append({
                        "query": description,
                        "duration": duration,
                        "status": "success"
                    })
                except Exception as e:
                    results.append({
                        "query": description,
                        "duration": 0,
                        "status": f"error: {str(e)}"
                    })
        
        # Display results
        table = Table(title="Database Performance")
        table.add_column("Query", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("Status", style="yellow")
        
        for result in results:
            table.add_row(
                result["query"],
                f"{result['duration']:.3f}s" if result['duration'] > 0 else "N/A",
                result["status"]
            )
        
        console.print(table)
    
    async def generate_prometheus_metrics(self) -> bytes:
        """Generate Prometheus metrics."""
        # Update gauges based on current metrics
        for key, metrics in self.metrics.items():
            endpoint = metrics.endpoint
            error_rate.labels(endpoint=endpoint).set(100 - metrics.success_rate)
            
            if metrics.cache_hits + metrics.cache_misses > 0:
                cache_hit_rate.set(metrics.cache_hit_rate)
        
        return generate_latest()


@click.command()
@click.option('--base-url', default='http://localhost:8000', help='API base URL')
@click.option('--api-key', help='API key for authentication')
@click.option('--full-scan', is_flag=True, help='Scan all endpoints from OpenAPI spec')
@click.option('--endpoint', help='Monitor specific endpoint')
@click.option('--duration', type=int, default=60, help='Monitoring duration in seconds')
@click.option('--report', is_flag=True, help='Generate health report')
@click.option('--output', help='Output file for report')
@click.option('--format', type=click.Choice(['html', 'json', 'text']), default='html', help='Report format')
@click.option('--dashboard', is_flag=True, help='Run real-time monitoring dashboard')
@click.option('--stress-test', is_flag=True, help='Run stress test')
@click.option('--concurrent', type=int, default=100, help='Concurrent requests for stress test')
@click.option('--check-db', is_flag=True, help='Check database performance')
@click.option('--prometheus', is_flag=True, help='Export Prometheus metrics')
def main(base_url, api_key, full_scan, endpoint, duration, report, output, 
         format, dashboard, stress_test, concurrent, check_db, prometheus):
    """Mobius API Health Monitoring Tool"""
    
    async def run():
        monitor = APIHealthMonitor(base_url, api_key)
        await monitor.initialize()
        
        if full_scan:
            await monitor.run_full_scan()
        
        if endpoint:
            if stress_test:
                await monitor.stress_test(endpoint, concurrent, duration)
            elif dashboard:
                await monitor.monitor_endpoint_live(endpoint, duration)
            else:
                await monitor.test_endpoint(endpoint)
        
        if check_db:
            await monitor.check_database_performance()
        
        if report:
            report_content = monitor.generate_report(format)
            
            if output:
                with open(output, 'w') as f:
                    f.write(report_content)
                console.print(f"[green]✓ Report saved to {output}[/green]")
            else:
                console.print(report_content)
        
        if prometheus:
            metrics_data = await monitor.generate_prometheus_metrics()
            console.print(metrics_data.decode())
        
        # Display summary
        if not report and monitor.metrics:
            table = Table(title="API Health Summary")
            table.add_column("Endpoint", style="cyan")
            table.add_column("Method", style="magenta")
            table.add_column("Success Rate", style="green")
            table.add_column("Avg Response", style="yellow")
            
            for key, metrics in monitor.metrics.items():
                table.add_row(
                    metrics.endpoint,
                    metrics.method,
                    f"{metrics.success_rate:.2f}%",
                    f"{metrics.avg_response_time:.3f}s"
                )
            
            console.print(table)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
```

## Integration with FastAPI

Add middleware for tracking metrics:

```python
# app/middleware/health_metrics.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis
from typing import Callable

class HealthMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API health metrics."""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Track request start time
        start_time = time.time()
        
        # Get cache status before request
        cache_key = f"cache:{request.url.path}:{request.method}"
        was_cached = await self.redis.exists(cache_key)
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Cache-Hit"] = "true" if was_cached else "false"
        
        # Store metrics in Redis
        metrics_key = f"metrics:{request.url.path}:{request.method}"
        await self.redis.hincrby(metrics_key, "total_requests", 1)
        
        if 200 <= response.status_code < 300:
            await self.redis.hincrby(metrics_key, "successful_requests", 1)
        else:
            await self.redis.hincrby(metrics_key, "failed_requests", 1)
            await self.redis.hincrby(metrics_key, f"status_{response.status_code}", 1)
        
        # Store response time
        await self.redis.lpush(f"{metrics_key}:response_times", process_time)
        await self.redis.ltrim(f"{metrics_key}:response_times", 0, 999)  # Keep last 1000
        
        return response
```

## Dashboard Component

Create a real-time monitoring dashboard:

```python
# scripts/api_dashboard.py
import asyncio
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from datetime import datetime
import httpx

console = Console()

class APIDashboard:
    """Real-time API monitoring dashboard."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.metrics = {}
        self.alerts = []
    
    def create_layout(self) -> Layout:
        """Create dashboard layout."""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="metrics", ratio=2),
            Layout(name="alerts", ratio=1)
        )
        
        layout["metrics"].split_column(
            Layout(name="endpoints"),
            Layout(name="performance")
        )
        
        return layout
    
    def update_header(self, layout: Layout):
        """Update header section."""
        header_text = Text(
            f"Mobius API Health Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            style="bold blue"
        )
        layout["header"].update(Panel(header_text, title="Dashboard"))
    
    def update_endpoints(self, layout: Layout):
        """Update endpoints table."""
        table = Table(title="Endpoint Status")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Response Time", style="yellow")
        table.add_column("Success Rate", style="magenta")
        
        for endpoint, metrics in self.metrics.items():
            status = "🟢" if metrics.get("healthy", False) else "🔴"
            table.add_row(
                endpoint,
                status,
                f"{metrics.get('response_time', 0):.3f}s",
                f"{metrics.get('success_rate', 0):.1f}%"
            )
        
        layout["endpoints"].update(Panel(table, title="Endpoints"))
    
    def update_performance(self, layout: Layout):
        """Update performance metrics."""
        perf_text = Text()
        
        total_requests = sum(m.get("requests", 0) for m in self.metrics.values())
        avg_response = sum(m.get("response_time", 0) for m in self.metrics.values()) / max(len(self.metrics), 1)
        
        perf_text.append(f"Total Requests: {total_requests}\n", style="cyan")
        perf_text.append(f"Avg Response Time: {avg_response:.3f}s\n", style="yellow")
        perf_text.append(f"Active Endpoints: {len(self.metrics)}\n", style="green")
        
        layout["performance"].update(Panel(perf_text, title="Performance"))
    
    def update_alerts(self, layout: Layout):
        """Update alerts section."""
        alerts_text = Text()
        
        for alert in self.alerts[-10:]:  # Show last 10 alerts
            style = "red" if alert["severity"] == "critical" else "yellow"
            alerts_text.append(f"[{alert['time']}] {alert['message']}\n", style=style)
        
        layout["alerts"].update(Panel(alerts_text, title="Alerts"))
    
    def update_footer(self, layout: Layout):
        """Update footer section."""
        footer_text = Text(
            "Press Ctrl+C to exit | R: Refresh | C: Clear alerts",
            style="dim"
        )
        layout["footer"].update(Panel(footer_text))
    
    async def fetch_metrics(self):
        """Fetch current metrics from API."""
        try:
            async with httpx.AsyncClient() as client:
                # Fetch metrics endpoint (if available)
                response = await client.get(f"{self.base_url}/metrics")
                if response.status_code == 200:
                    self.metrics = response.json()
        except Exception as e:
            self.alerts.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "severity": "warning",
                "message": f"Failed to fetch metrics: {e}"
            })
    
    async def run(self):
        """Run the dashboard."""
        layout = self.create_layout()
        
        with Live(layout, refresh_per_second=1) as live:
            while True:
                await self.fetch_metrics()
                
                self.update_header(layout)
                self.update_endpoints(layout)
                self.update_performance(layout)
                self.update_alerts(layout)
                self.update_footer(layout)
                
                await asyncio.sleep(1)

if __name__ == "__main__":
    dashboard = APIDashboard()
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped.[/yellow]")
```

## Automated Testing Suite

Create comprehensive API tests:

```python
# tests/test_api_health.py
import pytest
import httpx
from fastapi.testclient import TestClient
from typing import Dict, List
import asyncio

class TestAPIHealth:
    """Comprehensive API health tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)
    
    def test_openapi_spec_available(self, client):
        """Test that OpenAPI spec is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
        assert "paths" in response.json()
    
    def test_all_endpoints_documented(self, client):
        """Test that all endpoints have documentation."""
        spec = client.get("/openapi.json").json()
        
        for path, methods in spec["paths"].items():
            for method, details in methods.items():
                assert "summary" in details, f"{method.upper()} {path} missing summary"
                assert "responses" in details, f"{method.upper()} {path} missing responses"
    
    @pytest.mark.parametrize("endpoint", [
        "/api/v1/contexts",
        "/api/v1/projects",
        "/api/v1/health"
    ])
    def test_endpoint_performance(self, client, endpoint):
        """Test endpoint response times."""
        response = client.get(endpoint)
        
        # Check response time header
        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        
        # Should respond within 200ms
        assert process_time < 0.2, f"{endpoint} took {process_time}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test API under concurrent load."""
        async def make_request(client, endpoint):
            return client.get(endpoint)
        
        # Make 100 concurrent requests
        tasks = [make_request(client, "/api/v1/health") for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 100, f"Only {success_count}/100 requests succeeded"
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make many requests quickly
        responses = []
        for _ in range(150):
            responses.append(client.get("/api/v1/contexts"))
        
        # Should get rate limited
        rate_limited = sum(1 for r in responses if r.status_code == 429)
        assert rate_limited > 0, "Rate limiting not working"
    
    def test_error_response_format(self, client):
        """Test standardized error responses."""
        # Test 404
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data or "message" in error_data
        
        # Test 400
        response = client.post("/api/v1/contexts", json={"invalid": "data"})
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
    
    def test_cors_headers(self, client):
        """Test CORS configuration."""
        response = client.options("/api/v1/contexts")
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers
    
    def test_security_headers(self, client):
        """Test security headers."""
        response = client.get("/api/v1/health")
        
        # Check security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
```

## Performance Monitoring Configuration

Add Prometheus configuration:

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'mobius-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - 'alerts.yml'
```

## Alert Rules

```yaml
# monitoring/alerts.yml
groups:
  - name: api_health
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          (sum(rate(api_requests_total{status=~"5.."}[5m])) by (endpoint)
          /
          sum(rate(api_requests_total[5m])) by (endpoint)) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"
          description: "Error rate is {{ $value | humanizePercentage }} for endpoint {{ $labels.endpoint }}"
      
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, 
            sum(rate(api_request_duration_seconds_bucket[5m])) by (endpoint, le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time on {{ $labels.endpoint }}"
          description: "95th percentile response time is {{ $value }}s for endpoint {{ $labels.endpoint }}"
      
      - alert: LowCacheHitRate
        expr: api_cache_hit_rate < 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}%"
```

## Usage Examples

```bash
# Full system health check
python scripts/api_health.py --full-scan --check-db --report --output reports/health.html

# Monitor specific endpoint with dashboard
python scripts/api_health.py --endpoint /api/v1/contexts --dashboard --duration 300

# Stress test critical endpoint
python scripts/api_health.py --endpoint /api/v1/contexts --stress-test --concurrent 500 --duration 60

# Generate JSON report for CI/CD
python scripts/api_health.py --full-scan --report --format json --output health.json

# Export Prometheus metrics
python scripts/api_health.py --prometheus > /var/lib/prometheus/node_exporter/api_metrics.prom

# Run automated health checks (cron job)
*/5 * * * * /usr/bin/python /app/scripts/api_health.py --full-scan --report --output /app/reports/health_$(date +\%Y\%m\%d_\%H\%M).html
```

## Integration with CI/CD

```yaml
# .github/workflows/api-health.yml
name: API Health Check

on:
  push:
    branches: [main, develop]
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours

jobs:
  health-check:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install httpx pytest-asyncio
      
      - name: Start API server
        run: |
          docker-compose up -d
          sleep 10  # Wait for services to start
      
      - name: Run health checks
        run: |
          python scripts/api_health.py --full-scan --report --format json --output health.json
          
      - name: Check health status
        run: |
          python -c "
          import json
          with open('health.json') as f:
              data = json.load(f)
          if data['overall_success_rate'] < 95:
              raise Exception(f'API health check failed: {data[\"overall_success_rate\"]}% success rate')
          "
      
      - name: Upload health report
        uses: actions/upload-artifact@v3
        with:
          name: api-health-report
          path: health.json
      
      - name: Send alerts on failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: 'API health check failed!'
```

This comprehensive API health monitoring system provides:

1. **Real-time monitoring** with live dashboards
2. **Comprehensive metrics** including response times, error rates, and cache performance
3. **API standards validation** for REST compliance
4. **Stress testing capabilities** for load testing
5. **Automated reporting** in multiple formats
6. **Integration with monitoring tools** like Prometheus
7. **CI/CD integration** for continuous health checking
8. **Alerting rules** for proactive issue detection

The system is designed specifically for the Mobius FastAPI backend with support for all the mentioned technologies including Redis caching, PostgreSQL, and the multi-tier architecture.