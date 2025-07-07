# Security Audit Command

Performs comprehensive security analysis of the Mobius platform, including vulnerability scanning, secret detection, compliance checking, and configuration security review.

## Usage

```bash
security_audit [options]
```

## Options

- `--type <audit-type>`: Type of security audit to perform
  - `full`: Complete security audit (default)
  - `sast`: Static Application Security Testing only
  - `secrets`: Secret detection only
  - `compliance`: Compliance checking only
  - `config`: Configuration security only
  - `containers`: Container security only
- `--severity <level>`: Minimum severity level to report (critical|high|medium|low|info)
- `--fix`: Attempt to automatically fix identified issues where possible
- `--report <format>`: Output format (console|json|html|sarif)
- `--output <file>`: Save report to file
- `--fail-on <level>`: Exit with error if issues of this severity or higher are found

## Examples

```bash
# Run full security audit
security_audit

# Run SAST analysis only with high severity filter
security_audit --type sast --severity high

# Run secret detection with automatic fixes
security_audit --type secrets --fix

# Generate HTML report for compliance
security_audit --type compliance --report html --output security-report.html

# Fail CI/CD pipeline on critical issues
security_audit --fail-on critical
```

## Security Checks Performed

### 1. Static Application Security Testing (SAST)

#### Python/FastAPI Backend
- **Tool**: Bandit
- **Checks**:
  - SQL injection vulnerabilities
  - Command injection risks
  - Insecure deserialization
  - Hardcoded passwords/secrets
  - Weak cryptographic algorithms
  - Path traversal vulnerabilities
  - XML external entity (XXE) attacks
  - Server-side request forgery (SSRF)

#### JavaScript/TypeScript Frontend
- **Tools**: ESLint with security plugins, Semgrep
- **Checks**:
  - Cross-site scripting (XSS) vulnerabilities
  - Insecure direct object references
  - DOM-based vulnerabilities
  - Unsafe React patterns
  - Prototype pollution
  - Regular expression denial of service (ReDoS)
  - Insecure randomness

### 2. Secret Detection

#### Source Code Scanning
- **Tools**: GitLeaks, TruffleHog
- **Checks**:
  - API keys and tokens
  - Database credentials
  - Private keys and certificates
  - AWS/GCP/Azure credentials
  - OAuth secrets
  - JWT secrets
  - Webhook URLs with embedded tokens

#### Git History Analysis
- **Checks**:
  - Previously committed secrets
  - Deleted files containing secrets
  - Modified files with removed secrets
  - Branch-specific secrets

#### Environment Configuration
- **Checks**:
  - `.env` file security
  - Environment variable patterns
  - Configuration file permissions
  - Kubernetes secrets usage

### 3. Container Security

#### Image Scanning
- **Tool**: Trivy
- **Checks**:
  - OS package vulnerabilities
  - Application dependency vulnerabilities
  - Misconfigurations
  - Exposed secrets in layers
  - Insecure base images

#### Dockerfile Analysis
- **Checks**:
  - Running as root user
  - Unnecessary privileges
  - Exposed sensitive ports
  - Insecure package installations
  - Missing security updates

### 4. Infrastructure as Code Security

#### Kubernetes Manifests
- **Tools**: Kubesec, Polaris
- **Checks**:
  - Security contexts
  - Network policies
  - RBAC configurations
  - Pod security policies
  - Resource limits
  - Privileged containers

#### Terraform/IaC
- **Tool**: Checkov
- **Checks**:
  - Encrypted storage
  - Network security groups
  - IAM policies
  - Public exposure
  - Logging and monitoring

### 5. Security Compliance

#### OWASP Top 10 Compliance
- **A01:2021 – Broken Access Control**
  - Authorization bypass checks
  - Path traversal prevention
  - CORS misconfiguration
  
- **A02:2021 – Cryptographic Failures**
  - Weak encryption algorithms
  - Insecure key storage
  - Missing encryption at rest
  
- **A03:2021 – Injection**
  - SQL injection prevention
  - NoSQL injection checks
  - Command injection protection
  - LDAP injection prevention
  
- **A04:2021 – Insecure Design**
  - Threat modeling coverage
  - Security requirements validation
  - Secure design patterns
  
- **A05:2021 – Security Misconfiguration**
  - Default credentials
  - Unnecessary features enabled
  - Error handling disclosure
  - Security headers
  
- **A06:2021 – Vulnerable Components**
  - Dependency vulnerabilities
  - Outdated libraries
  - Unmaintained packages
  
- **A07:2021 – Authentication Failures**
  - Weak password policies
  - Session management
  - Multi-factor authentication
  
- **A08:2021 – Software and Data Integrity**
  - CI/CD security
  - Code signing
  - Dependency integrity
  
- **A09:2021 – Security Logging**
  - Audit logging coverage
  - Log injection prevention
  - Sensitive data in logs
  
- **A10:2021 – SSRF**
  - URL validation
  - Request filtering
  - Network segmentation

#### Security Headers Analysis
- **Checks**:
  - Content-Security-Policy (CSP)
  - X-Frame-Options
  - X-Content-Type-Options
  - Strict-Transport-Security (HSTS)
  - X-XSS-Protection
  - Referrer-Policy
  - Permissions-Policy

### 6. API Security

#### Endpoint Analysis
- **Checks**:
  - Authentication requirements
  - Authorization implementation
  - Rate limiting
  - Input validation
  - Output encoding
  - CORS configuration

#### GraphQL Security
- **Checks**:
  - Query depth limiting
  - Query complexity analysis
  - Introspection disable in production
  - Field-level authorization

### 7. Database Security

#### PostgreSQL Configuration
- **Checks**:
  - Encrypted connections
  - Strong authentication
  - Least privilege access
  - Audit logging
  - Backup encryption

#### Vector Database Security
- **Checks**:
  - Access control
  - API key rotation
  - Network isolation
  - Query injection prevention

### 8. Authentication & Authorization

#### OAuth2/JWT Implementation
- **Checks**:
  - Token expiration
  - Signature verification
  - Algorithm confusion attacks
  - Token storage security
  - Refresh token rotation

#### Session Management
- **Checks**:
  - Secure session cookies
  - Session fixation prevention
  - Concurrent session limits
  - Session timeout

## Security Tools Integration

### Required Tools

```bash
# Python security
pip install bandit safety

# JavaScript/TypeScript security
npm install -g eslint-plugin-security @typescript-eslint/eslint-plugin

# Container security
brew install aquasecurity/trivy/trivy

# Secret detection
brew install gitleaks
pip install truffleHog3

# Kubernetes security
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Infrastructure security
pip install checkov
```

### Tool Configuration

#### Bandit Configuration (.bandit)
```yaml
skips: []
tests: []
exclude_dirs:
  - /tests/
  - /venv/
  - /.venv/
```

#### ESLint Security Configuration
```json
{
  "extends": [
    "plugin:security/recommended"
  ],
  "plugins": ["security"],
  "rules": {
    "security/detect-object-injection": "error",
    "security/detect-non-literal-regexp": "error",
    "security/detect-unsafe-regex": "error"
  }
}
```

#### GitLeaks Configuration (.gitleaks.toml)
```toml
[allowlist]
paths = [
  "poetry.lock",
  "package-lock.json",
  "yarn.lock"
]

[[rules]]
id = "mobius-api-key"
description = "Mobius API Key"
regex = '''(?i)(mobius[_-]?api[_-]?key\s*[=:]\s*["']?)([a-zA-Z0-9]{32,})'''
```

## Remediation Guidelines

### Critical Issues
1. **Hardcoded Secrets**
   - Move to environment variables
   - Use secret management service
   - Rotate compromised credentials

2. **SQL Injection**
   - Use parameterized queries
   - Implement input validation
   - Apply least privilege database access

3. **XSS Vulnerabilities**
   - Sanitize user input
   - Use Content Security Policy
   - Encode output properly

### High Priority Issues
1. **Outdated Dependencies**
   - Update to latest stable versions
   - Review breaking changes
   - Test thoroughly after updates

2. **Insecure Authentication**
   - Implement MFA
   - Use secure session management
   - Apply proper password policies

3. **Missing Security Headers**
   - Configure all recommended headers
   - Test with securityheaders.com
   - Monitor for policy violations

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Security Audit
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Security Audit
        run: |
          # Install tools
          pip install bandit safety gitleaks
          npm install -g eslint-plugin-security
          
          # Run audit
          ./security_audit.sh --fail-on high
          
      - name: Upload Results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: security-report.sarif
```

### Pre-commit Hook
```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", "src/"]
        
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

## Reporting

### Console Output Format
```
🔒 Mobius Security Audit Report
================================
Scan Date: 2024-01-15 10:30:00
Total Issues Found: 23

Critical: 2
High: 5
Medium: 8
Low: 8

CRITICAL Issues:
----------------
[SEC001] Hardcoded database password found
  File: src/config/database.py:45
  Fix: Move to environment variable

[SEC002] SQL injection vulnerability
  File: src/api/search.py:123
  Fix: Use parameterized query

HIGH Issues:
------------
[SEC101] Outdated dependency with known vulnerabilities
  Package: requests==2.20.0
  Fix: Update to requests>=2.31.0
```

### JSON Report Format
```json
{
  "scan_date": "2024-01-15T10:30:00Z",
  "summary": {
    "total_issues": 23,
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 8
  },
  "issues": [
    {
      "id": "SEC001",
      "severity": "critical",
      "type": "hardcoded-secret",
      "file": "src/config/database.py",
      "line": 45,
      "description": "Hardcoded database password found",
      "remediation": "Move to environment variable",
      "cwe": "CWE-798"
    }
  ]
}
```

## Best Practices

1. **Run Regularly**
   - Schedule daily security scans
   - Run on every pull request
   - Perform deep scans weekly

2. **Progressive Enhancement**
   - Start with critical issues
   - Address high priority next
   - Plan for medium/low issues

3. **Security as Code**
   - Version control security policies
   - Automate security testing
   - Track security metrics

4. **Team Integration**
   - Security training for developers
   - Clear remediation guidelines
   - Security champions program

## Monitoring & Alerting

### Security Metrics
- Mean time to remediation (MTTR)
- Number of vulnerabilities by severity
- Security debt trend
- Compliance score

### Alert Thresholds
- Critical: Immediate notification
- High: Within 24 hours
- Medium: Within 1 week
- Low: Monthly review

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Security Headers](https://securityheaders.com/)
- [Mozilla Observatory](https://observatory.mozilla.org/)