# Container Health Commands - Mobius Platform

## Docker Health

### Image Size Optimization Analysis
```bash
# Analyze image sizes and layers
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" | sort -k3 -hr

# Detailed layer analysis for specific image
docker history --no-trunc mobius-backend:latest

# Compare image sizes across versions
docker images mobius-* --format "{{.Repository}}:{{.Tag}} {{.Size}}" | sort -k2 -hr

# Analyze multi-stage build efficiency
docker build --target build -t mobius-build-stage . && \
docker build --target runtime -t mobius-runtime-stage . && \
echo "Build stage: $(docker images mobius-build-stage --format '{{.Size}}')" && \
echo "Runtime stage: $(docker images mobius-runtime-stage --format '{{.Size}}')"

# Find unused images and calculate space savings
docker images -f dangling=true --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### Layer Caching Effectiveness
```bash
# Check build cache usage
docker system df -v | grep -A 10 "Build Cache"

# Analyze cache hit ratio during builds
docker build --progress=plain --no-cache=false . 2>&1 | grep -E "(CACHED|COPY|RUN)"

# Monitor layer reuse across builds
docker build --cache-from mobius-backend:latest -t mobius-backend:new .

# Inspect BuildKit cache
docker buildx du --verbose
```

### Security Vulnerability Scanning
```bash
# Scan with Trivy
trivy image --severity HIGH,CRITICAL mobius-backend:latest
trivy image --security-checks vuln,config mobius-frontend:latest

# Scan with Docker Scout
docker scout cves mobius-backend:latest
docker scout recommendations mobius-backend:latest

# Check for outdated base images
docker scout compare mobius-backend:latest --to mobius-backend:previous

# Scan all project images
for img in $(docker images 'mobius-*' --format "{{.Repository}}:{{.Tag}}"); do
    echo "Scanning $img..."
    trivy image --severity HIGH,CRITICAL --quiet $img
done
```

### Multi-stage Build Efficiency
```bash
# Measure build times for each stage
time docker build --target dependencies -t mobius-deps .
time docker build --target build -t mobius-build .
time docker build --target runtime -t mobius-runtime .

# Analyze space savings from multi-stage builds
docker images mobius-* --format "{{.Repository}}:{{.Tag}} {{.Size}}" | grep -E "(deps|build|runtime)"

# Check for unnecessary files in final image
docker run --rm mobius-backend:latest find / -name "*.pyc" -o -name "__pycache__" -o -name "*.log" 2>/dev/null | wc -l
```

## Kubernetes Health

### Pod Health and Restart Patterns
```bash
# Check pod status across all namespaces
kubectl get pods -A -o wide | grep -E "(mobius|Error|CrashLoop|Pending)"

# Analyze restart patterns
kubectl get pods -n mobius -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[*].restartCount,AGE:.metadata.creationTimestamp

# Get detailed pod events
kubectl describe pods -n mobius | grep -A 5 -B 5 "Events:"

# Check pod health history
kubectl get events -n mobius --sort-by='.lastTimestamp' | grep -E "(Unhealthy|Failed|Error)"

# Monitor pod lifecycle events
kubectl get events -n mobius --field-selector reason=Unhealthy,reason=BackOff -w
```

### Resource Utilization (CPU/Memory)
```bash
# Current resource usage
kubectl top nodes
kubectl top pods -n mobius --containers

# Resource requests vs actual usage
kubectl get pods -n mobius -o custom-columns=NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,MEM_LIM:.spec.containers[*].resources.limits.memory

# Historical resource metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/mobius/pods | jq '.items[] | {name: .metadata.name, cpu: .containers[].usage.cpu, memory: .containers[].usage.memory}'

# Resource pressure analysis
kubectl describe nodes | grep -A 5 "Allocated resources:"

# Identify resource bottlenecks
kubectl get pods -n mobius -o json | jq -r '.items[] | select(.status.phase == "Pending") | {name: .metadata.name, reason: .status.conditions[].reason}'
```

### Service Mesh Health Metrics
```bash
# Check Istio/Linkerd service mesh status
kubectl get pods -n istio-system
istioctl proxy-status

# Service mesh traffic metrics
kubectl exec -n mobius deployment/mobius-backend -c istio-proxy -- curl -s localhost:15000/stats/prometheus | grep -E "envoy_cluster_upstream_rq_total|envoy_cluster_upstream_rq_retry|envoy_cluster_upstream_rq_timeout"

# Circuit breaker status
kubectl exec -n mobius deployment/mobius-backend -c istio-proxy -- curl -s localhost:15000/clusters | grep -E "circuit_breakers|ejection"

# Service mesh configuration validation
istioctl analyze -n mobius
```

### Network Policy Effectiveness
```bash
# List all network policies
kubectl get networkpolicies -n mobius -o wide

# Test network policy enforcement
kubectl run test-pod --image=busybox -n mobius -it --rm -- wget -qO- http://mobius-backend:8000/health

# Analyze network policy coverage
kubectl get pods -n mobius -o json | jq -r '.items[].metadata.name' | while read pod; do
    echo "Pod: $pod"
    kubectl get networkpolicies -n mobius -o json | jq -r --arg pod "$pod" '.items[] | select(.spec.podSelector.matchLabels | to_entries[] | select(.key == "app" and .value == $pod)) | .metadata.name'
done

# Monitor denied connections
kubectl logs -n kube-system -l k8s-app=calico-node | grep -i "denied"
```

## Container Performance

### Startup Time Analysis
```bash
# Measure container startup times
kubectl get events -n mobius --field-selector reason=Started -o custom-columns=TIME:.firstTimestamp,POD:.involvedObject.name,MESSAGE:.message | sort

# Analyze init container performance
kubectl get pods -n mobius -o json | jq -r '.items[] | select(.spec.initContainers != null) | {name: .metadata.name, initContainers: [.spec.initContainers[].name], initDuration: .status.initContainerStatuses[].state.terminated.finishedAt}'

# Check readiness probe timing
kubectl describe pods -n mobius | grep -A 3 "Readiness:"

# Monitor startup probe failures
kubectl get events -n mobius --field-selector reason=Unhealthy | grep "Startup probe failed"
```

### Resource Limit Optimization
```bash
# Analyze OOMKilled events
kubectl get pods -n mobius -o json | jq -r '.items[] | select(.status.containerStatuses[]?.state.terminated.reason == "OOMKilled") | .metadata.name'

# Check CPU throttling
kubectl top pods -n mobius --containers | awk 'NR>1 {if ($3 > 80) print "High CPU: " $1 " - " $3 "%"}'

# Resource efficiency score
kubectl get pods -n mobius -o json | jq -r '.items[] | {
    name: .metadata.name,
    cpu_efficiency: ((.spec.containers[].resources.requests.cpu // "0m" | rtrimstr("m") | tonumber) / (.spec.containers[].resources.limits.cpu // "1000m" | rtrimstr("m") | tonumber) * 100),
    mem_efficiency: ((.spec.containers[].resources.requests.memory // "0Mi" | rtrimstr("Mi") | tonumber) / (.spec.containers[].resources.limits.memory // "1000Mi" | rtrimstr("Mi") | tonumber) * 100)
}'

# VPA recommendations
kubectl get vpa -n mobius -o json | jq -r '.items[] | {name: .metadata.name, recommendations: .status.recommendation.containerRecommendations}'
```

### Container Runtime Metrics
```bash
# Container runtime info
kubectl get nodes -o json | jq -r '.items[].status.nodeInfo.containerRuntimeVersion' | sort | uniq -c

# Runtime performance metrics
crictl stats

# Container filesystem usage
kubectl exec -n mobius deployment/mobius-backend -- df -h

# Check container process limits
kubectl exec -n mobius deployment/mobius-backend -- cat /proc/1/limits
```

### Storage Volume Performance
```bash
# List all PVCs and their status
kubectl get pvc -n mobius -o wide

# Storage usage analysis
kubectl exec -n mobius deployment/mobius-backend -- df -h | grep -E "(Filesystem|/data|/cache)"

# IOPS monitoring
kubectl exec -n mobius deployment/mobius-backend -- iostat -x 1 5

# Check for storage pressure
kubectl describe pvc -n mobius | grep -E "(Events|Warning|Failed)"

# Volume snapshot status
kubectl get volumesnapshots -n mobius
```

## Multi-Region Deployment

### Regional Deployment Status
```bash
# Check deployments across regions
for region in us-east-1 eu-west-1 ap-southeast-1; do
    echo "Region: $region"
    kubectl --context=mobius-$region get deployments -n mobius
done

# Verify regional pod distribution
kubectl get pods -n mobius -o json | jq -r '.items[] | {name: .metadata.name, node: .spec.nodeName, zone: .metadata.labels."topology.kubernetes.io/zone"}'

# Check regional service endpoints
kubectl get endpoints -n mobius -o wide

# Regional health check
for region in us-east-1 eu-west-1 ap-southeast-1; do
    echo "Health check for $region:"
    kubectl --context=mobius-$region get pods -n mobius --field-selector=status.phase!=Running
done
```

### Cross-Region Latency
```bash
# Measure cross-region API latency
kubectl exec -n mobius deployment/mobius-backend -- curl -w "@curl-format.txt" -o /dev/null -s https://mobius-eu.example.com/health

# Network latency between regions
kubectl exec -n mobius deployment/mobius-backend -- ping -c 10 mobius-backend.eu-west-1.svc.cluster.local | tail -n 1

# Database replication lag
kubectl exec -n mobius deployment/postgres-primary -- psql -U mobius -c "SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn FROM pg_stat_replication;"

# Service mesh cross-region metrics
istioctl proxy-config cluster deployment/mobius-backend -n mobius | grep -E "region|zone"
```

### Load Balancer Health
```bash
# Check load balancer status
kubectl get ingress -n mobius -o wide
kubectl describe ingress -n mobius | grep -A 10 "Events:"

# Backend health status
kubectl get endpoints -n mobius -o json | jq -r '.items[] | {name: .metadata.name, addresses: .subsets[].addresses[].ip}'

# Load balancer metrics
kubectl exec -n ingress-nginx deployment/nginx-ingress-controller -- curl -s http://localhost:10254/metrics | grep -E "nginx_ingress_controller_requests|nginx_ingress_controller_response_duration_seconds"

# SSL certificate status
kubectl get certificates -n mobius
kubectl describe certificate mobius-tls -n mobius | grep -A 5 "Status:"
```

### Ingress Controller Metrics
```bash
# Ingress controller status
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/nginx-ingress-controller --tail=50 | grep -E "error|Error"

# Request rate and errors
kubectl exec -n ingress-nginx deployment/nginx-ingress-controller -- curl -s http://localhost:10254/metrics | grep -E "nginx_ingress_controller_requests_total|nginx_ingress_controller_request_duration_seconds"

# Configuration validation
kubectl exec -n ingress-nginx deployment/nginx-ingress-controller -- nginx -t

# Active connections
kubectl exec -n ingress-nginx deployment/nginx-ingress-controller -- curl -s http://localhost:10254/nginx_status
```

## Monitoring Dashboard Commands

### Prometheus Queries
```bash
# High-level platform metrics
kubectl exec -n monitoring deployment/prometheus -- promtool query instant 'sum(rate(container_cpu_usage_seconds_total{namespace="mobius"}[5m])) by (pod)'

# Memory usage trends
kubectl exec -n monitoring deployment/prometheus -- promtool query instant 'sum(container_memory_working_set_bytes{namespace="mobius"}) by (pod) / 1024 / 1024'

# API latency percentiles
kubectl exec -n monitoring deployment/prometheus -- promtool query instant 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{namespace="mobius"}[5m]))'
```

### Grafana Dashboard Setup
```bash
# Import Mobius dashboards
kubectl exec -n monitoring deployment/grafana -- grafana-cli dashboards import 13659
kubectl exec -n monitoring deployment/grafana -- grafana-cli dashboards import 15760

# Configure alerts
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: mobius-alerts
  namespace: monitoring
data:
  alerts.yaml: |
    groups:
    - name: mobius
      rules:
      - alert: HighMemoryUsage
        expr: container_memory_working_set_bytes{namespace="mobius"} / container_spec_memory_limit_bytes > 0.9
        for: 5m
      - alert: PodRestartingFrequently
        expr: rate(kube_pod_container_status_restarts_total{namespace="mobius"}[15m]) > 0.1
        for: 5m
EOF
```

## Troubleshooting Commands

### Container Debugging
```bash
# Debug failing container
kubectl debug -n mobius deployment/mobius-backend -it --image=busybox --target=mobius-backend

# Copy files from container for analysis
# Define environment variables for paths, with sensible defaults
# MOBIUS_LOG_DIR=${MOBIUS_LOG_DIR:-/var/log/mobius}
# MOBIUS_TMP_DIR=${MOBIUS_TMP_DIR:-/tmp}
# Example: kubectl cp mobius/mobius-backend-xxx:"$MOBIUS_LOG_DIR"/mobius.log ./mobius-debug.log

# Run diagnostic commands
kubectl exec -n mobius deployment/mobius-backend -- python -m pip list
kubectl exec -n mobius deployment/mobius-backend -- python -c "import sys; print(sys.path)"
```

### Performance Profiling
```bash
# CPU profiling
# Example: kubectl exec -n mobius deployment/mobius-backend -- python -m cProfile -o "$MOBIUS_TMP_DIR"/profile.prof app.py
# kubectl cp mobius/mobius-backend-xxx:"$MOBIUS_TMP_DIR"/profile.prof ./profile.prof

# Memory profiling
kubectl exec -n mobius deployment/mobius-backend -- python -m memory_profiler app.py

# Network debugging
# Example: kubectl exec -n mobius deployment/mobius-backend -- tcpdump -i any -w "$MOBIUS_TMP_DIR"/capture.pcap
# kubectl cp mobius/mobius-backend-xxx:"$MOBIUS_TMP_DIR"/capture.pcap
```

## Automation Scripts

### Health Check Script
```bash
#!/bin/bash
# Save as check_container_health.sh

echo "=== Mobius Container Health Check ==="
echo "Timestamp: $(date)"

# Check Docker images
echo -e "\n--- Docker Images ---"
docker images mobius-* --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Check Kubernetes pods
echo -e "\n--- Pod Status ---"
kubectl get pods -n mobius -o wide

# Check resource usage
echo -e "\n--- Resource Usage ---"
kubectl top pods -n mobius

# Check recent events
echo -e "\n--- Recent Events ---"
kubectl get events -n mobius --sort-by='.lastTimestamp' | head -20

# Check ingress
echo -e "\n--- Ingress Status ---"
kubectl get ingress -n mobius

echo -e "\n=== Health Check Complete ==="
```

### Automated Remediation
```bash
#!/bin/bash
# Save as auto_remediate.sh

# Restart pods with high restart count
kubectl get pods -n mobius -o json | jq -r '.items[] | select(.status.containerStatuses[].restartCount > 5) | .metadata.name' | while read pod; do
    echo "Restarting pod with high restart count: $pod"
    kubectl delete pod -n mobius $pod
done

# Clean up evicted pods
kubectl get pods -n mobius --field-selector=status.phase=Failed -o name | xargs kubectl delete -n mobius

# Scale down and up deployments with issues
kubectl get deployments -n mobius -o json | jq -r '.items[] | select(.status.conditions[] | select(.type=="Progressing" and .status=="False")) | .metadata.name' | while read deploy; do
    echo "Recycling deployment: $deploy"
    kubectl scale deployment -n mobius $deploy --replicas=0
    sleep 5
    kubectl scale deployment -n mobius $deploy --replicas=3
done
```
