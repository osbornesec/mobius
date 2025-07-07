# Error Tracking and Log Analysis Command

Comprehensive error tracking and log analysis for the Mobius Context Engineering Platform.

## Usage

```bash
# Basic error analysis
claude run error_tracking.md

# Analyze specific time range
claude run error_tracking.md --since "1 hour ago" --until now

# Focus on specific error types
claude run error_tracking.md --error-type "DatabaseError,APIError"

# Generate error report
claude run error_tracking.md --report --output error_report.html

# Real-time monitoring mode
claude run error_tracking.md --monitor --threshold critical

# Analyze specific service logs
claude run error_tracking.md --service api --service frontend
```

## Error Analysis

### 1. Error Frequency Analysis

```python
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import subprocess

class ErrorAnalyzer:
    """Analyze error patterns and frequencies"""
    
    def __init__(self, log_dir: str = "/var/log/mobius"):
        self.log_dir = Path(log_dir)
        self.error_patterns = {
            'database': r'(DatabaseError|psycopg2|SQLAlchemy)',
            'api': r'(FastAPI|HTTPException|RequestValidationError)',
            'vector_db': r'(Qdrant|Pinecone|vector)',
            'auth': r'(JWT|OAuth|AuthenticationError)',
            'network': r'(ConnectionError|TimeoutError|NetworkError)',
            'memory': r'(MemoryError|OutOfMemory)',
            'validation': r'(ValidationError|Pydantic)',
            'frontend': r'(React|TypeError|ReferenceError)'
        }
        
    def analyze_error_frequency(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict:
        """Analyze error frequency by type and severity"""
        errors = defaultdict(lambda: {'count': 0, 'severity': Counter(), 'messages': []})
        
        for log_file in self.get_log_files(time_range):
            with open(log_file, 'r') as f:
                for line in f:
                    error_info = self.parse_error_line(line)
                    if error_info:
                        error_type = error_info['type']
                        errors[error_type]['count'] += 1
                        errors[error_type]['severity'][error_info['severity']] += 1
                        errors[error_type]['messages'].append(error_info['message'][:100])
        
        return self.generate_frequency_report(errors)
    
    def parse_error_line(self, line: str) -> Optional[Dict]:
        """Parse error information from log line"""
        # Standard log format: [timestamp] [level] [service] message
        match = re.match(r'\[(.*?)\] \[(ERROR|CRITICAL|WARNING)\] \[(.*?)\] (.*)', line)
        if not match:
            return None
            
        timestamp, severity, service, message = match.groups()
        
        # Classify error type
        error_type = 'unknown'
        for category, pattern in self.error_patterns.items():
            if re.search(pattern, message, re.I):
                error_type = category
                break
                
        return {
            'timestamp': timestamp,
            'severity': severity,
            'service': service,
            'type': error_type,
            'message': message
        }
    
    def analyze_stack_traces(self) -> Dict[str, List[Dict]]:
        """Identify and group similar stack traces"""
        stack_traces = defaultdict(list)
        current_trace = []
        trace_key = None
        
        for log_file in self.get_log_files():
            with open(log_file, 'r') as f:
                for line in f:
                    if 'Traceback' in line:
                        if current_trace and trace_key:
                            stack_traces[trace_key].append({
                                'trace': '\n'.join(current_trace),
                                'count': 1
                            })
                        current_trace = [line.strip()]
                        trace_key = None
                    elif current_trace:
                        current_trace.append(line.strip())
                        if 'Error:' in line:
                            # Use error message as key for grouping
                            trace_key = re.sub(r'[0-9]+', 'N', line.strip())
        
        return self.group_similar_traces(stack_traces)
    
    def detect_error_trends(self, window_size: int = 3600) -> Dict:
        """Detect error trends over time"""
        time_buckets = defaultdict(lambda: defaultdict(int))
        
        for log_file in self.get_log_files():
            with open(log_file, 'r') as f:
                for line in f:
                    error_info = self.parse_error_line(line)
                    if error_info:
                        timestamp = datetime.fromisoformat(error_info['timestamp'])
                        bucket = timestamp.replace(minute=0, second=0, microsecond=0)
                        time_buckets[bucket][error_info['type']] += 1
        
        return self.calculate_trends(time_buckets)
```

### 2. Critical Error Detection

```python
class CriticalErrorDetector:
    """Detect and alert on critical errors"""
    
    def __init__(self):
        self.critical_patterns = [
            {'pattern': r'OutOfMemoryError', 'category': 'resource', 'severity': 'critical'},
            {'pattern': r'Database connection lost', 'category': 'database', 'severity': 'critical'},
            {'pattern': r'Authentication bypass', 'category': 'security', 'severity': 'critical'},
            {'pattern': r'Data corruption', 'category': 'data', 'severity': 'critical'},
            {'pattern': r'Service crash', 'category': 'availability', 'severity': 'critical'},
            {'pattern': r'Infinite loop detected', 'category': 'performance', 'severity': 'critical'}
        ]
        
    def scan_for_critical_errors(self, log_files: List[Path]) -> List[Dict]:
        """Scan logs for critical error patterns"""
        critical_errors = []
        
        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern_info in self.critical_patterns:
                        if re.search(pattern_info['pattern'], line, re.I):
                            critical_errors.append({
                                'file': str(log_file),
                                'line': line_num,
                                'category': pattern_info['category'],
                                'severity': pattern_info['severity'],
                                'message': line.strip(),
                                'timestamp': self.extract_timestamp(line)
                            })
        
        return sorted(critical_errors, key=lambda x: x['timestamp'], reverse=True)
```

## Log Analysis

### 1. Log Level Distribution

```python
class LogAnalyzer:
    """Comprehensive log analysis"""
    
    def __init__(self):
        self.log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        self.services = ['api', 'frontend', 'worker', 'scheduler', 'vector_db']
        
    def analyze_log_distribution(self) -> Dict:
        """Analyze log level distribution across services"""
        distribution = defaultdict(lambda: Counter())
        
        for service in self.services:
            log_files = Path(f"/var/log/mobius/{service}").glob("*.log")
            for log_file in log_files:
                with open(log_file, 'r') as f:
                    for line in f:
                        level = self.extract_log_level(line)
                        if level:
                            distribution[service][level] += 1
        
        return self.calculate_percentages(distribution)
    
    def analyze_log_volume(self, time_window: int = 3600) -> Dict:
        """Analyze log volume metrics"""
        volume_metrics = {
            'total_lines': 0,
            'lines_per_second': 0,
            'size_mb': 0,
            'by_service': {},
            'by_level': Counter(),
            'peak_times': []
        }
        
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=time_window)
        
        for service in self.services:
            service_metrics = self.calculate_service_volume(service, start_time, end_time)
            volume_metrics['by_service'][service] = service_metrics
            volume_metrics['total_lines'] += service_metrics['lines']
            
        volume_metrics['lines_per_second'] = volume_metrics['total_lines'] / time_window
        
        return volume_metrics
    
    def analyze_performance_logs(self) -> Dict:
        """Extract and analyze performance metrics from logs"""
        perf_metrics = {
            'response_times': [],
            'query_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'slow_queries': [],
            'memory_spikes': []
        }
        
        # Pattern for FastAPI response times
        response_pattern = r'Response time: (\d+\.?\d*)ms'
        query_pattern = r'Query executed in (\d+\.?\d*)ms'
        memory_pattern = r'Memory usage: (\d+\.?\d*)MB'
        
        for log_file in Path("/var/log/mobius/api").glob("*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    # Extract response times
                    match = re.search(response_pattern, line)
                    if match:
                        time_ms = float(match.group(1))
                        perf_metrics['response_times'].append(time_ms)
                        if time_ms > 200:  # Threshold from requirements
                            perf_metrics['slow_queries'].append({
                                'time': time_ms,
                                'context': line.strip()
                            })
                    
                    # Extract query times
                    match = re.search(query_pattern, line)
                    if match:
                        perf_metrics['query_times'].append(float(match.group(1)))
                    
                    # Extract memory usage
                    match = re.search(memory_pattern, line)
                    if match:
                        memory_mb = float(match.group(1))
                        perf_metrics['memory_usage'].append(memory_mb)
                        if memory_mb > 1024:  # 1GB spike threshold
                            perf_metrics['memory_spikes'].append({
                                'usage': memory_mb,
                                'context': line.strip()
                            })
        
        return self.calculate_performance_stats(perf_metrics)
```

### 2. Security Event Detection

```python
class SecurityEventDetector:
    """Detect security-related events in logs"""
    
    def __init__(self):
        self.security_patterns = {
            'auth_failure': r'(Authentication failed|Invalid credentials|JWT expired)',
            'permission_denied': r'(Permission denied|Unauthorized access|Forbidden)',
            'suspicious_activity': r'(Multiple failed attempts|Brute force|SQL injection)',
            'data_access': r'(Sensitive data accessed|Bulk export|Admin access)',
            'api_abuse': r'(Rate limit exceeded|Unusual API pattern|DDoS)',
            'injection_attempt': r'(SQL injection|XSS attempt|Command injection)'
        }
        
    def scan_security_events(self) -> Dict[str, List[Dict]]:
        """Scan logs for security events"""
        security_events = defaultdict(list)
        
        for log_file in Path("/var/log/mobius").rglob("*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    for event_type, pattern in self.security_patterns.items():
                        if re.search(pattern, line, re.I):
                            event = self.parse_security_event(line, event_type)
                            if event:
                                security_events[event_type].append(event)
        
        return self.analyze_security_patterns(security_events)
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalous security patterns"""
        anomalies = []
        
        # Detect rapid authentication failures
        auth_failures = self.get_events_by_type('auth_failure')
        anomalies.extend(self.detect_rapid_failures(auth_failures))
        
        # Detect unusual access patterns
        access_events = self.get_events_by_type('data_access')
        anomalies.extend(self.detect_unusual_access(access_events))
        
        # Detect potential attacks
        attack_events = self.get_events_by_type('injection_attempt')
        anomalies.extend(self.detect_attack_patterns(attack_events))
        
        return sorted(anomalies, key=lambda x: x['risk_score'], reverse=True)
```

## Application Monitoring

### 1. FastAPI Exception Tracking

```python
class FastAPIMonitor:
    """Monitor FastAPI application errors"""
    
    def __init__(self):
        self.exception_types = {
            'HTTPException': 'http',
            'RequestValidationError': 'validation',
            'DatabaseError': 'database',
            'TimeoutError': 'timeout',
            'AuthenticationError': 'auth'
        }
        
    def track_exceptions(self) -> Dict:
        """Track FastAPI exceptions"""
        exceptions = defaultdict(lambda: {
            'count': 0,
            'endpoints': Counter(),
            'status_codes': Counter(),
            'recent_examples': []
        })
        
        api_logs = Path("/var/log/mobius/api").glob("*.log")
        for log_file in api_logs:
            with open(log_file, 'r') as f:
                for line in f:
                    exception_info = self.parse_fastapi_exception(line)
                    if exception_info:
                        exc_type = exception_info['type']
                        exceptions[exc_type]['count'] += 1
                        exceptions[exc_type]['endpoints'][exception_info['endpoint']] += 1
                        exceptions[exc_type]['status_codes'][exception_info['status_code']] += 1
                        
                        if len(exceptions[exc_type]['recent_examples']) < 5:
                            exceptions[exc_type]['recent_examples'].append({
                                'timestamp': exception_info['timestamp'],
                                'message': exception_info['message'],
                                'endpoint': exception_info['endpoint']
                            })
        
        return dict(exceptions)
    
    def analyze_endpoint_errors(self) -> Dict[str, Dict]:
        """Analyze errors by API endpoint"""
        endpoint_errors = defaultdict(lambda: {
            'total_errors': 0,
            'error_rate': 0,
            'error_types': Counter(),
            'avg_response_time': 0
        })
        
        # Parse API access logs
        access_logs = Path("/var/log/mobius/api/access.log")
        if access_logs.exists():
            total_requests = defaultdict(int)
            error_requests = defaultdict(int)
            
            with open(access_logs, 'r') as f:
                for line in f:
                    log_entry = self.parse_access_log(line)
                    if log_entry:
                        endpoint = log_entry['endpoint']
                        total_requests[endpoint] += 1
                        
                        if log_entry['status'] >= 400:
                            error_requests[endpoint] += 1
                            endpoint_errors[endpoint]['total_errors'] += 1
                            endpoint_errors[endpoint]['error_types'][log_entry['status']] += 1
            
            # Calculate error rates
            for endpoint in total_requests:
                if total_requests[endpoint] > 0:
                    error_rate = error_requests[endpoint] / total_requests[endpoint]
                    endpoint_errors[endpoint]['error_rate'] = error_rate
        
        return dict(endpoint_errors)
```

### 2. React Error Boundary Analysis

```python
class ReactErrorMonitor:
    """Monitor React frontend errors"""
    
    def __init__(self):
        self.error_boundaries = []
        self.browser_logs = Path("/var/log/mobius/frontend/browser.log")
        
    def analyze_error_boundaries(self) -> Dict:
        """Analyze React error boundary catches"""
        boundary_errors = {
            'total_catches': 0,
            'by_component': Counter(),
            'by_error_type': Counter(),
            'recovery_success': 0,
            'user_impact': []
        }
        
        if self.browser_logs.exists():
            with open(self.browser_logs, 'r') as f:
                for line in f:
                    if 'ErrorBoundary' in line:
                        error_info = self.parse_error_boundary(line)
                        if error_info:
                            boundary_errors['total_catches'] += 1
                            boundary_errors['by_component'][error_info['component']] += 1
                            boundary_errors['by_error_type'][error_info['error_type']] += 1
                            
                            if error_info['recovered']:
                                boundary_errors['recovery_success'] += 1
                            
                            if error_info['user_visible']:
                                boundary_errors['user_impact'].append({
                                    'component': error_info['component'],
                                    'impact': error_info['impact_description']
                                })
        
        return boundary_errors
    
    def track_client_errors(self) -> Dict:
        """Track client-side JavaScript errors"""
        client_errors = {
            'syntax_errors': [],
            'runtime_errors': [],
            'network_errors': [],
            'promise_rejections': [],
            'by_browser': Counter(),
            'by_page': Counter()
        }
        
        # Parse browser console logs
        console_pattern = r'\[(.*?)\] (.*Error): (.*) at (.*)'
        
        with open(self.browser_logs, 'r') as f:
            for line in f:
                match = re.match(console_pattern, line)
                if match:
                    timestamp, error_type, message, location = match.groups()
                    
                    error_entry = {
                        'timestamp': timestamp,
                        'type': error_type,
                        'message': message,
                        'location': location,
                        'user_agent': self.extract_user_agent(line)
                    }
                    
                    if 'SyntaxError' in error_type:
                        client_errors['syntax_errors'].append(error_entry)
                    elif 'NetworkError' in error_type or 'Failed to fetch' in message:
                        client_errors['network_errors'].append(error_entry)
                    elif 'Unhandled Promise' in message:
                        client_errors['promise_rejections'].append(error_entry)
                    else:
                        client_errors['runtime_errors'].append(error_entry)
                    
                    # Track by browser
                    browser = self.detect_browser(error_entry['user_agent'])
                    client_errors['by_browser'][browser] += 1
                    
                    # Track by page
                    page = self.extract_page_from_location(location)
                    client_errors['by_page'][page] += 1
        
        return client_errors
```

### 3. Database Error Patterns

```python
class DatabaseErrorMonitor:
    """Monitor database-related errors"""
    
    def __init__(self):
        self.db_types = ['postgresql', 'qdrant', 'pinecone', 'redis']
        
    def analyze_database_errors(self) -> Dict:
        """Analyze database error patterns"""
        db_errors = {
            'connection_errors': defaultdict(list),
            'query_errors': defaultdict(list),
            'timeout_errors': defaultdict(list),
            'constraint_violations': defaultdict(list),
            'deadlocks': defaultdict(list),
            'performance_issues': defaultdict(list)
        }
        
        for db_type in self.db_types:
            log_path = Path(f"/var/log/mobius/{db_type}")
            if log_path.exists():
                for log_file in log_path.glob("*.log"):
                    with open(log_file, 'r') as f:
                        for line in f:
                            error_category = self.categorize_db_error(line)
                            if error_category:
                                error_info = self.parse_db_error(line, db_type)
                                db_errors[error_category][db_type].append(error_info)
        
        return self.generate_db_error_summary(db_errors)
    
    def detect_connection_pool_issues(self) -> List[Dict]:
        """Detect connection pool exhaustion and leaks"""
        pool_issues = []
        
        # PostgreSQL connection pool monitoring
        pg_logs = Path("/var/log/mobius/postgresql/postgresql.log")
        if pg_logs.exists():
            with open(pg_logs, 'r') as f:
                connection_count = 0
                max_connections = 100  # From config
                
                for line in f:
                    if 'connection authorized' in line:
                        connection_count += 1
                    elif 'disconnection' in line:
                        connection_count -= 1
                    
                    if connection_count > max_connections * 0.8:
                        pool_issues.append({
                            'type': 'pool_exhaustion',
                            'database': 'postgresql',
                            'usage': connection_count / max_connections,
                            'timestamp': self.extract_timestamp(line)
                        })
        
        return pool_issues
```

### 4. External API Failure Tracking

```python
class ExternalAPIMonitor:
    """Monitor external API integrations"""
    
    def __init__(self):
        self.external_apis = {
            'openai': 'https://api.openai.com',
            'anthropic': 'https://api.anthropic.com',
            'github': 'https://api.github.com',
            'gitlab': 'https://gitlab.com/api',
            'slack': 'https://slack.com/api'
        }
        
    def track_api_failures(self) -> Dict:
        """Track external API failures and patterns"""
        api_failures = defaultdict(lambda: {
            'total_failures': 0,
            'failure_rate': 0,
            'status_codes': Counter(),
            'error_types': Counter(),
            'avg_response_time': [],
            'recent_failures': []
        })
        
        # Parse API client logs
        api_logs = Path("/var/log/mobius/api/external_calls.log")
        if api_logs.exists():
            with open(api_logs, 'r') as f:
                for line in f:
                    api_call = self.parse_api_call(line)
                    if api_call and not api_call['success']:
                        api_name = self.identify_api(api_call['url'])
                        if api_name:
                            api_failures[api_name]['total_failures'] += 1
                            api_failures[api_name]['status_codes'][api_call['status_code']] += 1
                            api_failures[api_name]['error_types'][api_call['error_type']] += 1
                            
                            if len(api_failures[api_name]['recent_failures']) < 10:
                                api_failures[api_name]['recent_failures'].append({
                                    'timestamp': api_call['timestamp'],
                                    'endpoint': api_call['endpoint'],
                                    'error': api_call['error_message']
                                })
        
        return dict(api_failures)
    
    def analyze_retry_patterns(self) -> Dict:
        """Analyze API retry patterns and effectiveness"""
        retry_analysis = {
            'total_retries': 0,
            'successful_retries': 0,
            'retry_chains': [],
            'exponential_backoff_compliance': 0,
            'circuit_breaker_triggers': []
        }
        
        retry_pattern = r'Retry attempt (\d+) for (.*) after (\d+)ms'
        success_pattern = r'Retry successful for (.*) after (\d+) attempts'
        circuit_pattern = r'Circuit breaker opened for (.*)'
        
        with open("/var/log/mobius/api/external_calls.log", 'r') as f:
            current_retry_chain = None
            
            for line in f:
                # Track retry attempts
                retry_match = re.search(retry_pattern, line)
                if retry_match:
                    attempt, endpoint, delay = retry_match.groups()
                    retry_analysis['total_retries'] += 1
                    
                    if current_retry_chain and current_retry_chain['endpoint'] == endpoint:
                        current_retry_chain['attempts'].append({
                            'attempt': int(attempt),
                            'delay': int(delay)
                        })
                    else:
                        current_retry_chain = {
                            'endpoint': endpoint,
                            'attempts': [{'attempt': int(attempt), 'delay': int(delay)}],
                            'success': False
                        }
                
                # Track successful retries
                success_match = re.search(success_pattern, line)
                if success_match:
                    retry_analysis['successful_retries'] += 1
                    if current_retry_chain:
                        current_retry_chain['success'] = True
                        retry_analysis['retry_chains'].append(current_retry_chain)
                        current_retry_chain = None
                
                # Track circuit breaker triggers
                circuit_match = re.search(circuit_pattern, line)
                if circuit_match:
                    api_name = circuit_match.group(1)
                    retry_analysis['circuit_breaker_triggers'].append({
                        'api': api_name,
                        'timestamp': self.extract_timestamp(line)
                    })
        
        return retry_analysis
```

## Alerting & Reporting

### 1. Error Threshold Monitoring

```python
class ErrorThresholdMonitor:
    """Monitor error thresholds and trigger alerts"""
    
    def __init__(self):
        self.thresholds = {
            'error_rate': {
                'warning': 0.05,  # 5% error rate
                'critical': 0.10  # 10% error rate
            },
            'response_time': {
                'warning': 200,   # 200ms (from requirements)
                'critical': 500   # 500ms
            },
            'memory_usage': {
                'warning': 0.80,  # 80% of available
                'critical': 0.90  # 90% of available
            },
            'concurrent_errors': {
                'warning': 10,    # 10 errors per minute
                'critical': 50    # 50 errors per minute
            }
        }
        
    def check_thresholds(self) -> List[Dict]:
        """Check all thresholds and return violations"""
        violations = []
        
        # Check error rate threshold
        error_rate = self.calculate_current_error_rate()
        if error_rate > self.thresholds['error_rate']['critical']:
            violations.append({
                'metric': 'error_rate',
                'severity': 'critical',
                'current_value': error_rate,
                'threshold': self.thresholds['error_rate']['critical'],
                'message': f'Critical error rate: {error_rate:.2%}'
            })
        elif error_rate > self.thresholds['error_rate']['warning']:
            violations.append({
                'metric': 'error_rate',
                'severity': 'warning',
                'current_value': error_rate,
                'threshold': self.thresholds['error_rate']['warning'],
                'message': f'High error rate: {error_rate:.2%}'
            })
        
        # Check response time threshold
        avg_response_time = self.calculate_avg_response_time()
        if avg_response_time > self.thresholds['response_time']['critical']:
            violations.append({
                'metric': 'response_time',
                'severity': 'critical',
                'current_value': avg_response_time,
                'threshold': self.thresholds['response_time']['critical'],
                'message': f'Critical response time: {avg_response_time}ms'
            })
        
        # Check memory usage
        memory_usage = self.get_current_memory_usage()
        if memory_usage > self.thresholds['memory_usage']['critical']:
            violations.append({
                'metric': 'memory_usage',
                'severity': 'critical',
                'current_value': memory_usage,
                'threshold': self.thresholds['memory_usage']['critical'],
                'message': f'Critical memory usage: {memory_usage:.1%}'
            })
        
        return violations
    
    def create_alert(self, violation: Dict) -> Dict:
        """Create alert for threshold violation"""
        alert = {
            'id': self.generate_alert_id(),
            'timestamp': datetime.now().isoformat(),
            'severity': violation['severity'],
            'metric': violation['metric'],
            'message': violation['message'],
            'current_value': violation['current_value'],
            'threshold': violation['threshold'],
            'recommended_actions': self.get_recommended_actions(violation),
            'notification_channels': self.get_notification_channels(violation['severity'])
        }
        
        return alert
```

### 2. Automated Error Reports

```python
class ErrorReportGenerator:
    """Generate comprehensive error reports"""
    
    def __init__(self):
        self.report_template = """
# Mobius Error Analysis Report
Generated: {timestamp}
Period: {start_time} to {end_time}

## Executive Summary
- Total Errors: {total_errors}
- Error Rate: {error_rate:.2%}
- Critical Issues: {critical_count}
- Top Error Type: {top_error_type} ({top_error_count} occurrences)

## Error Distribution
{error_distribution}

## Critical Issues
{critical_issues}

## Performance Impact
{performance_impact}

## Recommendations
{recommendations}

## Detailed Analysis
{detailed_analysis}
"""
        
    def generate_report(self, time_range: Tuple[datetime, datetime]) -> str:
        """Generate comprehensive error report"""
        # Collect all metrics
        error_analyzer = ErrorAnalyzer()
        log_analyzer = LogAnalyzer()
        db_monitor = DatabaseErrorMonitor()
        api_monitor = ExternalAPIMonitor()
        
        # Analyze errors
        error_freq = error_analyzer.analyze_error_frequency(time_range)
        error_trends = error_analyzer.detect_error_trends()
        stack_traces = error_analyzer.analyze_stack_traces()
        
        # Analyze performance
        perf_logs = log_analyzer.analyze_performance_logs()
        
        # Analyze databases
        db_errors = db_monitor.analyze_database_errors()
        
        # Analyze external APIs
        api_failures = api_monitor.track_api_failures()
        
        # Generate report sections
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'start_time': time_range[0].isoformat(),
            'end_time': time_range[1].isoformat(),
            'total_errors': sum(e['count'] for e in error_freq.values()),
            'error_rate': self.calculate_error_rate(error_freq, time_range),
            'critical_count': self.count_critical_errors(error_freq),
            'top_error_type': self.get_top_error_type(error_freq),
            'top_error_count': self.get_top_error_count(error_freq),
            'error_distribution': self.format_error_distribution(error_freq),
            'critical_issues': self.format_critical_issues(error_freq, stack_traces),
            'performance_impact': self.format_performance_impact(perf_logs),
            'recommendations': self.generate_recommendations(error_freq, perf_logs, db_errors),
            'detailed_analysis': self.format_detailed_analysis(
                error_freq, error_trends, stack_traces, db_errors, api_failures
            )
        }
        
        return self.report_template.format(**report_data)
    
    def generate_html_report(self, report_data: Dict) -> str:
        """Generate HTML version of error report with charts"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Mobius Error Analysis Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 20px; 
                   border: 1px solid #ddd; border-radius: 5px; }}
        .critical {{ background-color: #fee; }}
        .warning {{ background-color: #ffd; }}
        .chart-container {{ width: 600px; margin: 20px 0; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Mobius Error Analysis Report</h1>
    <p>Generated: {timestamp}</p>
    
    <div class="metrics">
        <div class="metric {error_severity}">
            <h3>Error Rate</h3>
            <p>{error_rate:.2%}</p>
        </div>
        <div class="metric">
            <h3>Total Errors</h3>
            <p>{total_errors}</p>
        </div>
        <div class="metric critical">
            <h3>Critical Issues</h3>
            <p>{critical_count}</p>
        </div>
    </div>
    
    <div class="chart-container">
        <canvas id="errorTrendChart"></canvas>
    </div>
    
    <div class="chart-container">
        <canvas id="errorTypeChart"></canvas>
    </div>
    
    <h2>Top Issues</h2>
    <table>
        <tr>
            <th>Error Type</th>
            <th>Count</th>
            <th>Severity</th>
            <th>Trend</th>
        </tr>
        {error_table_rows}
    </table>
    
    <h2>Recommendations</h2>
    {recommendations_html}
    
    <script>
        // Error trend chart
        const trendCtx = document.getElementById('errorTrendChart').getContext('2d');
        new Chart(trendCtx, {{
            type: 'line',
            data: {error_trend_data},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Error Trend Over Time'
                    }}
                }}
            }}
        }});
        
        // Error type distribution
        const typeCtx = document.getElementById('errorTypeChart').getContext('2d');
        new Chart(typeCtx, {{
            type: 'doughnut',
            data: {error_type_data},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Error Distribution by Type'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html_template.format(**report_data)
```

### 3. Error Correlation Analysis

```python
class ErrorCorrelationAnalyzer:
    """Analyze correlations between different error types"""
    
    def __init__(self):
        self.correlation_window = 300  # 5 minutes
        
    def analyze_error_correlations(self) -> Dict:
        """Find correlations between different error types"""
        error_events = self.collect_error_events()
        
        correlations = {
            'temporal_correlations': self.find_temporal_correlations(error_events),
            'causal_chains': self.identify_causal_chains(error_events),
            'service_correlations': self.find_service_correlations(error_events),
            'user_impact_correlations': self.analyze_user_impact(error_events)
        }
        
        return correlations
    
    def find_temporal_correlations(self, events: List[Dict]) -> List[Dict]:
        """Find errors that tend to occur together"""
        correlations = []
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda x: x['timestamp'])
        
        # Look for patterns within time windows
        for i, event in enumerate(sorted_events):
            window_start = event['timestamp']
            window_end = window_start + timedelta(seconds=self.correlation_window)
            
            # Find all events in the same window
            window_events = [
                e for e in sorted_events[i+1:]
                if window_start <= e['timestamp'] <= window_end
            ]
            
            if len(window_events) >= 2:
                # Calculate correlation strength
                correlation = {
                    'primary_error': event['type'],
                    'correlated_errors': [e['type'] for e in window_events],
                    'correlation_strength': len(window_events) / self.correlation_window,
                    'time_window': self.correlation_window,
                    'examples': [event] + window_events[:3]
                }
                correlations.append(correlation)
        
        return self.aggregate_correlations(correlations)
    
    def identify_causal_chains(self, events: List[Dict]) -> List[Dict]:
        """Identify potential causal relationships between errors"""
        causal_patterns = [
            {
                'cause': 'database_connection',
                'effects': ['api_timeout', 'user_error'],
                'delay': 5
            },
            {
                'cause': 'memory_spike',
                'effects': ['performance_degradation', 'timeout'],
                'delay': 30
            },
            {
                'cause': 'external_api_failure',
                'effects': ['retry_storm', 'queue_backup'],
                'delay': 60
            }
        ]
        
        causal_chains = []
        
        for pattern in causal_patterns:
            cause_events = [e for e in events if pattern['cause'] in e['type']]
            
            for cause_event in cause_events:
                # Look for effect events within the delay window
                effect_window_start = cause_event['timestamp']
                effect_window_end = effect_window_start + timedelta(seconds=pattern['delay'])
                
                effect_events = [
                    e for e in events
                    if any(effect in e['type'] for effect in pattern['effects'])
                    and effect_window_start <= e['timestamp'] <= effect_window_end
                ]
                
                if effect_events:
                    causal_chains.append({
                        'cause': cause_event,
                        'effects': effect_events,
                        'pattern': pattern,
                        'confidence': len(effect_events) / len(pattern['effects'])
                    })
        
        return causal_chains
```

### 4. Root Cause Suggestions

```python
class RootCauseSuggester:
    """Suggest potential root causes for errors"""
    
    def __init__(self):
        self.knowledge_base = {
            'database_connection': {
                'symptoms': ['connection refused', 'timeout', 'connection pool exhausted'],
                'potential_causes': [
                    'Database server down',
                    'Network connectivity issues',
                    'Connection pool misconfiguration',
                    'Database overload',
                    'Firewall blocking connections'
                ],
                'diagnostic_steps': [
                    'Check database server status',
                    'Verify network connectivity',
                    'Review connection pool settings',
                    'Check database load metrics',
                    'Review firewall rules'
                ]
            },
            'memory_error': {
                'symptoms': ['OutOfMemoryError', 'memory allocation failed', 'heap space'],
                'potential_causes': [
                    'Memory leak in application',
                    'Insufficient memory allocation',
                    'Large data processing without streaming',
                    'Cache size too large',
                    'Too many concurrent requests'
                ],
                'diagnostic_steps': [
                    'Analyze heap dumps',
                    'Review memory allocation settings',
                    'Check for unbounded collections',
                    'Monitor garbage collection',
                    'Profile memory usage'
                ]
            },
            'api_timeout': {
                'symptoms': ['request timeout', 'gateway timeout', '504 error'],
                'potential_causes': [
                    'Slow database queries',
                    'External API latency',
                    'CPU-intensive operations',
                    'Network congestion',
                    'Insufficient resources'
                ],
                'diagnostic_steps': [
                    'Profile slow queries',
                    'Check external API response times',
                    'Monitor CPU usage',
                    'Review network metrics',
                    'Check resource allocation'
                ]
            }
        }
        
    def suggest_root_causes(self, error_pattern: Dict) -> Dict:
        """Suggest potential root causes based on error patterns"""
        suggestions = {
            'error_type': error_pattern['type'],
            'confidence': 0,
            'potential_causes': [],
            'diagnostic_steps': [],
            'related_metrics': [],
            'historical_solutions': []
        }
        
        # Match error pattern to knowledge base
        for error_type, knowledge in self.knowledge_base.items():
            symptom_match = sum(
                1 for symptom in knowledge['symptoms']
                if symptom.lower() in error_pattern['message'].lower()
            )
            
            if symptom_match > 0:
                match_confidence = symptom_match / len(knowledge['symptoms'])
                
                if match_confidence > suggestions['confidence']:
                    suggestions['confidence'] = match_confidence
                    suggestions['potential_causes'] = knowledge['potential_causes']
                    suggestions['diagnostic_steps'] = knowledge['diagnostic_steps']
        
        # Add contextual information
        suggestions['related_metrics'] = self.get_related_metrics(error_pattern)
        suggestions['historical_solutions'] = self.find_historical_solutions(error_pattern)
        
        return suggestions
    
    def generate_diagnostic_script(self, error_type: str) -> str:
        """Generate diagnostic script for specific error type"""
        scripts = {
            'database_connection': '''#!/bin/bash
# Database Connection Diagnostic Script

echo "Checking database connectivity..."
pg_isready -h $DB_HOST -p $DB_PORT

echo "Testing connection pool..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "SELECT count(*) FROM pg_stat_activity;"

echo "Checking active connections..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "
SELECT pid, usename, application_name, client_addr, state, 
       state_change, query_start, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;"

echo "Checking for long-running queries..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"
''',
            'memory_error': '''#!/bin/bash
# Memory Diagnostic Script

echo "Current memory usage..."
free -h

echo "Top memory consumers..."
ps aux --sort=-%mem | head -20

echo "Java heap usage (if applicable)..."
jstat -gc $(pgrep java) || echo "No Java process found"

echo "Python memory usage..."
python3 -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"

echo "Container memory limits..."
cat /proc/self/cgroup | grep memory || echo "Not running in container"
''',
            'api_timeout': '''#!/bin/bash
# API Timeout Diagnostic Script

echo "Checking API response times..."
for i in {1..5}; do
    time curl -s -o /dev/null -w "%{http_code} %{time_total}s\\n" http://localhost:8000/health
    sleep 1
done

echo "Checking external API connectivity..."
for api in "api.openai.com" "api.anthropic.com"; do
    echo "Testing $api..."
    time curl -s -o /dev/null -w "%{http_code} %{time_total}s\\n" https://$api/health || echo "Failed"
done

echo "Database query performance..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"
'''
        }
        
        return scripts.get(error_type, '# No diagnostic script available')
```

## Main Execution

```python
def main():
    """Main execution function for error tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mobius Error Tracking and Analysis')
    parser.add_argument('--since', default='1 hour ago', help='Start time for analysis')
    parser.add_argument('--until', default='now', help='End time for analysis')
    parser.add_argument('--error-type', help='Filter by error type')
    parser.add_argument('--service', help='Filter by service')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--monitor', action='store_true', help='Real-time monitoring mode')
    parser.add_argument('--threshold', choices=['warning', 'critical'], help='Alert threshold')
    
    args = parser.parse_args()
    
    # Parse time range
    start_time = parse_time_string(args.since)
    end_time = parse_time_string(args.until)
    time_range = (start_time, end_time)
    
    if args.monitor:
        # Real-time monitoring mode
        monitor = ErrorThresholdMonitor()
        print("Starting real-time error monitoring...")
        print(f"Alert threshold: {args.threshold or 'all'}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                violations = monitor.check_thresholds()
                
                for violation in violations:
                    if not args.threshold or violation['severity'] == args.threshold:
                        alert = monitor.create_alert(violation)
                        print(f"[{alert['timestamp']}] {alert['severity'].upper()}: {alert['message']}")
                        
                        # Send notifications
                        for channel in alert['notification_channels']:
                            send_notification(channel, alert)
                
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            print("\nStopping monitoring...")
    
    elif args.report:
        # Generate comprehensive report
        print("Generating error analysis report...")
        generator = ErrorReportGenerator()
        
        if args.output and args.output.endswith('.html'):
            # Generate HTML report
            report_data = generator.collect_report_data(time_range)
            report_content = generator.generate_html_report(report_data)
        else:
            # Generate text report
            report_content = generator.generate_report(time_range)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report_content)
            print(f"Report saved to: {args.output}")
        else:
            print(report_content)
    
    else:
        # Interactive analysis mode
        analyzer = ErrorAnalyzer()
        
        print("Analyzing errors...")
        error_freq = analyzer.analyze_error_frequency(time_range)
        
        # Filter by error type if specified
        if args.error_type:
            error_freq = {
                k: v for k, v in error_freq.items() 
                if args.error_type.lower() in k.lower()
            }
        
        # Display results
        print(f"\nError Analysis ({args.since} to {args.until}):")
        print("=" * 60)
        
        for error_type, data in sorted(error_freq.items(), 
                                     key=lambda x: x[1]['count'], 
                                     reverse=True):
            print(f"\n{error_type}:")
            print(f"  Total: {data['count']}")
            print(f"  Severity distribution: {dict(data['severity'])}")
            
            if data['recent_examples']:
                print("  Recent examples:")
                for example in data['recent_examples'][:3]:
                    print(f"    - {example}")
        
        # Analyze correlations
        print("\n\nError Correlations:")
        print("=" * 60)
        correlator = ErrorCorrelationAnalyzer()
        correlations = correlator.analyze_error_correlations()
        
        for correlation in correlations['temporal_correlations'][:5]:
            print(f"\n{correlation['primary_error']} often followed by:")
            for error in correlation['correlated_errors']:
                print(f"  - {error}")
            print(f"  Correlation strength: {correlation['correlation_strength']:.2f}")
        
        # Suggest root causes
        print("\n\nRoot Cause Analysis:")
        print("=" * 60)
        suggester = RootCauseSuggester()
        
        for error_type, data in list(error_freq.items())[:3]:
            if data['count'] > 10:  # Only analyze frequent errors
                suggestions = suggester.suggest_root_causes({
                    'type': error_type,
                    'message': data['recent_examples'][0] if data['recent_examples'] else ''
                })
                
                print(f"\n{error_type}:")
                print(f"  Confidence: {suggestions['confidence']:.2f}")
                print("  Potential causes:")
                for cause in suggestions['potential_causes'][:3]:
                    print(f"    - {cause}")
                print("  Diagnostic steps:")
                for step in suggestions['diagnostic_steps'][:3]:
                    print(f"    - {step}")


def parse_time_string(time_str: str) -> datetime:
    """Parse human-readable time strings"""
    if time_str == 'now':
        return datetime.now()
    
    # Parse relative times like "1 hour ago"
    match = re.match(r'(\d+)\s+(hour|minute|day)s?\s+ago', time_str)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'hour':
            return datetime.now() - timedelta(hours=amount)
        elif unit == 'minute':
            return datetime.now() - timedelta(minutes=amount)
        elif unit == 'day':
            return datetime.now() - timedelta(days=amount)
    
    # Try to parse as ISO format
    try:
        return datetime.fromisoformat(time_str)
    except:
        raise ValueError(f"Cannot parse time string: {time_str}")


def send_notification(channel: str, alert: Dict):
    """Send alert notification to specified channel"""
    if channel == 'slack':
        # Send to Slack webhook
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if webhook_url:
            requests.post(webhook_url, json={
                'text': f"{alert['severity'].upper()}: {alert['message']}",
                'attachments': [{
                    'color': 'danger' if alert['severity'] == 'critical' else 'warning',
                    'fields': [
                        {'title': 'Metric', 'value': alert['metric'], 'short': True},
                        {'title': 'Value', 'value': str(alert['current_value']), 'short': True},
                        {'title': 'Threshold', 'value': str(alert['threshold']), 'short': True},
                        {'title': 'Time', 'value': alert['timestamp'], 'short': True}
                    ]
                }]
            })
    
    elif channel == 'email':
        # Send email alert
        # Implementation depends on email service configuration
        pass
    
    elif channel == 'pagerduty':
        # Send to PagerDuty
        # Implementation depends on PagerDuty configuration
        pass


if __name__ == "__main__":
    main()
```

## Integration Examples

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment="production"
)

# Custom error tracking integration
class SentryErrorTracker:
    def capture_error(self, error_info: Dict):
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("error_type", error_info['type'])
            scope.set_level(error_info['severity'].lower())
            scope.set_context("error_details", {
                'service': error_info['service'],
                'endpoint': error_info.get('endpoint'),
                'user_id': error_info.get('user_id')
            })
            sentry_sdk.capture_message(error_info['message'])
```

### Prometheus Integration

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
error_counter = Counter('mobius_errors_total', 
                       'Total number of errors',
                       ['service', 'error_type', 'severity'])

response_time_histogram = Histogram('mobius_response_time_seconds',
                                  'Response time in seconds',
                                  ['method', 'endpoint'])

active_connections = Gauge('mobius_active_connections',
                         'Number of active connections',
                         ['service'])

# Use in error tracking
def track_error_metrics(error_info: Dict):
    error_counter.labels(
        service=error_info['service'],
        error_type=error_info['type'],
        severity=error_info['severity']
    ).inc()
```

### ELK Stack Integration

```python
from elasticsearch import Elasticsearch
import json

class ElasticsearchErrorTracker:
    def __init__(self):
        self.es = Elasticsearch(['http://localhost:9200'])
        self.index_name = 'mobius-errors'
        
    def index_error(self, error_info: Dict):
        """Index error in Elasticsearch"""
        doc = {
            'timestamp': error_info['timestamp'],
            'service': error_info['service'],
            'error_type': error_info['type'],
            'severity': error_info['severity'],
            'message': error_info['message'],
            'stack_trace': error_info.get('stack_trace'),
            'user_id': error_info.get('user_id'),
            'request_id': error_info.get('request_id'),
            'environment': 'production'
        }
        
        self.es.index(
            index=self.index_name,
            body=doc
        )
    
    def search_errors(self, query: Dict) -> List[Dict]:
        """Search errors in Elasticsearch"""
        results = self.es.search(
            index=self.index_name,
            body=query
        )
        
        return [hit['_source'] for hit in results['hits']['hits']]
```

This comprehensive error tracking command provides powerful error analysis, log monitoring, application tracking, and automated reporting capabilities for the Mobius platform.