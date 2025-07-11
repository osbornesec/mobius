# Database Health Monitoring Commands

## PostgreSQL Health Monitoring

### Connection Pool Status
```bash
# Check active connections and pool status
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    datname,
    count(*) as connections,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname, state, wait_event_type, wait_event
ORDER BY connections DESC;"

# Connection pool efficiency
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    max_conn,
    used,
    res_for_super,
    max_conn - used - res_for_super AS available
FROM
    (SELECT count(*) used FROM pg_stat_activity) t1,
    (SELECT setting::int res_for_super FROM pg_settings WHERE name='superuser_reserved_connections') t2,
    (SELECT setting::int max_conn FROM pg_settings WHERE name='max_connections') t3;"
```

### Query Performance Metrics
```bash
# Top 10 slowest queries
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    substring(query, 1, 100) as query_preview,
    mean_exec_time::numeric(10,2) as avg_ms,
    calls,
    total_exec_time::numeric(10,2) as total_ms,
    min_exec_time::numeric(10,2) as min_ms,
    max_exec_time::numeric(10,2) as max_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Query cache hit ratio
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;"
```

### Index Usage Analysis
```bash
# Unused indexes
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_relation_size(indexrelid) DESC;"

# Missing indexes (sequential scan heavy tables)
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / GREATEST(seq_scan, 1) as avg_seq_read
FROM pg_stat_user_tables
WHERE seq_scan > 100
AND seq_tup_read > 1000
ORDER BY seq_tup_read DESC
LIMIT 20;"
```

### Table Bloat Detection
```bash
# Table bloat analysis
psql -h localhost -U postgres -d mobius_db -c "
WITH constants AS (
    SELECT current_setting('block_size')::numeric AS bs, 23 AS hdr, 4 AS ma
),
bloat_info AS (
    SELECT
        ma,bs,schemaname,tablename,
        (datawidth+(hdr+ma-(CASE WHEN hdr%ma=0 THEN ma ELSE hdr%ma END)))::numeric AS datahdr,
        (maxfracsum*(nullhdr+ma-(CASE WHEN nullhdr%ma=0 THEN ma ELSE nullhdr%ma END))) AS nullhdr2
    FROM (
        SELECT
            schemaname, tablename, hdr, ma, bs,
            SUM((1-null_frac)*avg_width) AS datawidth,
            MAX(null_frac) AS maxfracsum,
            hdr+(
                SELECT 1+COUNT(*)/8
                FROM pg_stats s2
                WHERE null_frac<>0 AND s2.schemaname = s.schemaname AND s2.tablename = s.tablename
            ) AS nullhdr
        FROM pg_stats s, constants
        GROUP BY 1,2,3,4,5
    ) AS foo
),
table_bloat AS (
    SELECT
        schemaname, tablename, cc.relpages, bs,
        CEIL((cc.reltuples*((datahdr+ma-
            (CASE WHEN datahdr%ma=0 THEN ma ELSE datahdr%ma END))+nullhdr2+4))/(bs-20::float)) AS otta
    FROM bloat_info
    JOIN pg_class cc ON cc.relname = bloat_info.tablename
    JOIN pg_namespace nn ON cc.relnamespace = nn.oid AND nn.nspname = bloat_info.schemaname
)
SELECT
    schemaname,
    tablename,
    ROUND(100*((relpages-otta)::numeric/relpages),2) AS bloat_pct,
    pg_size_pretty((relpages-otta)*bs::bigint) AS bloat_size,
    pg_size_pretty(relpages*bs::bigint) AS table_size
FROM table_bloat
WHERE relpages > 100
AND (relpages-otta)::numeric/relpages > 0.2
ORDER BY (relpages-otta) DESC
LIMIT 10;"
```

### Slow Query Identification
```bash
# Currently running slow queries
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    state,
    substring(query, 1, 100) as query_preview
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state != 'idle'
ORDER BY duration DESC;"

# Lock monitoring
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.GRANTED;"
```

## Qdrant Vector DB Health

### Collection Statistics
```bash
# Get all collections info
curl -X GET "http://localhost:6333/collections" | jq '.'

# Specific collection details
curl -X GET "http://localhost:6333/collections/context_embeddings" | jq '.'

# Collection point count
curl -X GET "http://localhost:6333/collections/context_embeddings" | jq '.result.points_count'
```

### Search Performance Metrics
```bash
# Benchmark search performance
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import time
import requests
import numpy as np
import json

def benchmark_search(collection_name="context_embeddings", num_queries=100, vector_dim=1536):
    """Benchmark Qdrant search performance"""
    latencies = []

    for _ in range(num_queries):
        # Generate random vector
        vector = np.random.rand(vector_dim).tolist()

        # Time the search
        start = time.time()
        response = requests.post(
            f"http://localhost:6333/collections/{collection_name}/points/search",
            json={
                "vector": vector,
                "limit": 10,
                "with_payload": True
            }
        )
        end = time.time()

        if response.status_code == 200:
            latencies.append((end - start) * 1000)  # Convert to ms

    # Calculate statistics
    print(f"Search Performance for {collection_name}:")
    print(f"  Queries: {len(latencies)}")
    print(f"  Avg Latency: {np.mean(latencies):.2f}ms")
    print(f"  P50 Latency: {np.percentile(latencies, 50):.2f}ms")
    print(f"  P95 Latency: {np.percentile(latencies, 95):.2f}ms")
    print(f"  P99 Latency: {np.percentile(latencies, 99):.2f}ms")
    print(f"  Max Latency: {np.max(latencies):.2f}ms")

if __name__ == "__main__":
    benchmark_search()
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

### Index Optimization Status
```bash
# Check index status
curl -X GET "http://localhost:6333/collections/context_embeddings" | jq '.result.config.hnsw_config'

# Optimize collection
curl -X POST "http://localhost:6333/collections/context_embeddings/index" \
  -H "Content-Type: application/json" \
  -d '{
    "recreate_index": true
  }'
```

### Memory Usage Patterns
```bash
# Get Qdrant telemetry
curl -X GET "http://localhost:6333/telemetry" | jq '.'

# Monitor memory usage
docker stats qdrant --no-stream --format "table {{.Container}}	{{.MemUsage}}	{{.MemPerc}}"

# Collection memory footprint
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import requests
import json

def check_memory_usage():
    collections = requests.get("http://localhost:6333/collections").json()

    print("Qdrant Memory Usage by Collection:")
    print("-" * 60)

    for collection in collections['result']['collections']:
        name = collection['name']
        info = requests.get(f"http://localhost:6333/collections/{name}").json()

        points = info['result']['points_count']
        vector_size = info['result']['config']['params']['vectors']['size']

        # Estimate memory usage (rough calculation)
        memory_mb = (points * vector_size * 4) / (1024 * 1024)  # 4 bytes per float

        print(f"{name:30} Points: {points:10} Est. Memory: {memory_mb:.2f} MB")

if __name__ == "__main__":
    check_memory_usage()
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

## Redis Cache Health

### Cache Hit/Miss Rates
```bash
# Redis info stats
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"

# Calculate hit rate
redis-cli --raw INFO stats | awk -F: '
    /keyspace_hits:/ {hits=$2}
    /keyspace_misses:/ {misses=$2}
    END {
        total=hits+misses;
        if(total>0) {
            rate=(hits/total)*100;
            printf "Cache Hit Rate: %.2f%% (Hits: %d, Misses: %d)\n", rate, hits, misses
        }
    }'
```

### Memory Usage and Eviction
```bash
# Memory info
redis-cli INFO memory

# Eviction statistics
redis-cli INFO stats | grep evicted

# Memory usage by key pattern
redis-cli --bigkeys

# Memory doctor
redis-cli MEMORY DOCTOR

# Top keys by memory
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import redis
import sys

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def analyze_memory(pattern='*', limit=20):
    """Analyze Redis memory usage by key pattern"""
    keys = r.keys(pattern)
    key_sizes = []

    for key in keys[:1000]:  # Sample first 1000 keys
        try:
            memory = r.memory_usage(key)
            if memory:
                key_sizes.append((key, memory))
        except:
            pass

    # Sort by size
    key_sizes.sort(key=lambda x: x[1], reverse=True)

    print(f"Top {limit} keys by memory usage:")
    print("-" * 60)
    for key, size in key_sizes[:limit]:
        print(f"{key[:50]:50} {size:>10} bytes ({size/1024/1024:.2f} MB)")

if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else '*'
    analyze_memory(pattern)
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

### Key Expiration Patterns
```bash
# TTL distribution
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
#!/bin/bash

echo "Redis TTL Distribution Analysis"
echo "==============================="

redis-cli --raw KEYS "*" | while read key; do
    ttl=$(redis-cli TTL "$key" 2>/dev/null)
    echo $ttl
done | awk '
    BEGIN {no_ttl=0; expired=0; ttl_set=0}
    {
        if ($1 == -1) no_ttl++
        else if ($1 == -2) expired++
        else if ($1 > 0) {
            ttl_set++
            if ($1 < 60) bucket["<1min"]++
            else if ($1 < 3600) bucket["<1hour"]++
            else if ($1 < 86400) bucket["<1day"]++
            else bucket[">1day"]++
        }
    }
    END {
        print "No TTL set:", no_ttl
        print "Keys with TTL:", ttl_set
        print "\nTTL Distribution:"
        for (b in bucket) print "  " b ":", bucket[b]
    }'
EOF

bash $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

### Connection Pool Status
```bash
# Client connections
redis-cli CLIENT LIST | wc -l

# Connected clients info
redis-cli INFO clients

# Monitor real-time commands
redis-cli MONITOR  # Use Ctrl+C to stop

# Slow log
redis-cli SLOWLOG GET 10

# Connection pool health check
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import redis
from redis.connection import ConnectionPool
import time
import threading

def test_connection_pool(max_connections=50):
    """Test Redis connection pool behavior"""
    pool = ConnectionPool(host='localhost', port=6379, max_connections=max_connections)
    r = redis.Redis(connection_pool=pool)

    def worker(worker_id):
        try:
            start = time.time()
            r.ping()
            duration = (time.time() - start) * 1000
            print(f"Worker {worker_id}: Connected in {duration:.2f}ms")
        except Exception as e:
            print(f"Worker {worker_id}: Failed - {e}")

    # Create many concurrent connections
    threads = []
    for i in range(max_connections + 10):  # Exceed pool size
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Check pool stats
    print(f"\nPool Stats:")
    print(f"  Created Connections: {pool.created_connections}")
    print(f"  Max Connections: {pool.max_connections}")

if __name__ == "__main__":
    test_connection_pool()
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

## Migration & Schema Health

### Alembic Migration Status
```bash
# Check current migration version
cd /home/michael/dev/Mobius
alembic current

# Show migration history
alembic history --verbose

# Check pending migrations
alembic check

# Verify migration status
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import subprocess
import sys

def check_migration_status():
    """Check if there are pending migrations"""
    try:
        # Get current revision
        current = subprocess.check_output(['alembic', 'current'], text=True)

        # Get head revision
        head = subprocess.check_output(['alembic', 'heads'], text=True)

        # Compare
        if head.strip() in current:
            print("✅ Database is up to date with migrations")
            return True
        else:
            print("⚠️  Pending migrations detected!")
            print(f"Current: {current.strip()}")
            print(f"Head: {head.strip()}")

            # Show pending migrations
            subprocess.call(['alembic', 'history', '-r', f'current:heads'])
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking migrations: {e}")
        return False

if __name__ == "__main__":
    if not check_migration_status():
        sys.exit(1)
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

### Schema Version Tracking
```bash
# Check alembic version table
psql -h localhost -U postgres -d mobius_db -c "
SELECT version_num, branch_labels
FROM alembic_version;"

# Schema metadata
psql -h localhost -U postgres -d mobius_db -c "
SELECT
    table_schema,
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name;"
```

### Schema Drift Analysis
```bash
# Generate schema dump
TEMP_SCHEMA_FILE=$(mktemp)
pg_dump -h localhost -U postgres -d mobius_db --schema-only > $TEMP_SCHEMA_FILE

# Compare with expected schema
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
import subprocess
import sqlalchemy
from sqlalchemy import inspect
import difflib

def check_schema_drift():
    """Compare actual database schema with SQLAlchemy models"""

    # Connect to database
    engine = sqlalchemy.create_engine('postgresql://postgres:password@localhost/mobius_db')
    inspector = inspect(engine)

    # Get actual tables
    actual_tables = set(inspector.get_table_names())

    # Expected tables from models (update this list based on your models)
    expected_tables = {
        'users', 'contexts', 'documents', 'embeddings',
        'workspaces', 'tags', 'alembic_version'
    }

    # Find differences
    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables

    print("Schema Drift Analysis")
    print("=" * 50)

    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")

    if extra_tables:
        print(f"⚠️  Extra tables: {extra_tables}")

    if not missing_tables and not extra_tables:
        print("✅ All expected tables present")

    # Check column drift for common tables
    common_tables = actual_tables & expected_tables
    for table in common_tables:
        actual_columns = set(c['name'] for c in inspector.get_columns(table))
        # Compare with expected columns (would need to import models)
        print(f"\nTable '{table}' has {len(actual_columns)} columns")

if __name__ == "__main__":
    check_schema_drift()
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
rm $TEMP_SCHEMA_FILE
```

## Combined Health Dashboard

### Quick Health Check Script
```bash
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
#!/bin/bash

echo "🏥 Mobius Database Health Check"
echo "==============================="
echo

# PostgreSQL
echo "📊 PostgreSQL Status:"
psql -h localhost -U postgres -d mobius_db -t -c "
SELECT 'Active Connections: ' || count(*) FROM pg_stat_activity;" 2>/dev/null || echo "❌ PostgreSQL connection failed"

psql -h localhost -U postgres -d mobius_db -t -c "
SELECT 'Cache Hit Rate: ' || ROUND(100.0 * sum(heap_blks_hit) /
    (sum(heap_blks_hit) + sum(heap_blks_read)), 2) || '%'
FROM pg_statio_user_tables;" 2>/dev/null

echo

# Qdrant
echo "🔍 Qdrant Status:"
curl -s -X GET "http://localhost:6333/collections" | jq -r '.result.collections[] | "Collection: \(.name)"' 2>/dev/null || echo "❌ Qdrant connection failed"

echo

# Redis
echo "💾 Redis Status:"
redis-cli ping > /dev/null 2>&1 && echo "✅ Redis is running" || echo "❌ Redis connection failed"
redis-cli --raw INFO stats 2>/dev/null | awk -F: '
    /keyspace_hits:/ {hits=$2}
    /keyspace_misses:/ {misses=$2}
    END {
        if(hits+misses>0) {
            rate=(hits/(hits+misses))*100;
            printf "Cache Hit Rate: %.2f%%\n", rate
        }
    }'

echo

# Migrations
echo "🔄 Migration Status:"
cd /home/michael/dev/Mobius && alembic current 2>/dev/null | grep -q "head" && echo "✅ Migrations up to date" || echo "⚠️  Pending migrations"

echo
echo "==============================="
echo "Run specific sections above for detailed analysis"
EOF

chmod +x $TEMP_SCRIPT
$TEMP_SCRIPT
rm $TEMP_SCRIPT
```

### Performance Monitoring Script
```bash
TEMP_SCRIPT=$(mktemp)
cat > $TEMP_SCRIPT << 'EOF'
#!/usr/bin/env python3

import psycopg2
import redis
import requests
import time
import json
from datetime import datetime

class MobiusHealthMonitor:
    def __init__(self):
        self.pg_conn = psycopg2.connect(
            host="localhost",
            database="mobius_db",
            user="postgres",
            password="password"
        )
        self.redis_client = redis.Redis(host='localhost', port=6379)
        self.qdrant_url = "http://localhost:6333"

    def check_postgresql(self):
        """Check PostgreSQL health metrics"""
        cursor = self.pg_conn.cursor()

        # Query performance
        cursor.execute("""
            SELECT
                COALESCE(SUM(numbackends), 0) as connections,
                COALESCE(SUM(xact_commit), 0) as commits,
                COALESCE(SUM(xact_rollback), 0) as rollbacks
            FROM pg_stat_database
            WHERE datname = 'mobius_db'
        """)
        stats = cursor.fetchone()

        return {
            "connections": stats[0],
            "commits": stats[1],
            "rollbacks": stats[2],
            "status": "healthy" if stats[0] < 90 else "warning"
        }

    def check_redis(self):
        """Check Redis health metrics"""
        info = self.redis_client.info()

        hit_rate = 0
        if info['keyspace_hits'] + info['keyspace_misses'] > 0:
            hit_rate = (info['keyspace_hits'] /
                       (info['keyspace_hits'] + info['keyspace_misses'])) * 100

        return {
            "used_memory_mb": info['used_memory'] / 1024 / 1024,
            "connected_clients": info['connected_clients'],
            "hit_rate": round(hit_rate, 2),
            "evicted_keys": info.get('evicted_keys', 0),
            "status": "healthy" if hit_rate > 80 else "warning"
        }

    def check_qdrant(self):
        """Check Qdrant health metrics"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections")
            collections = response.json()['result']['collections']

            total_points = 0
            for collection in collections:
                coll_info = requests.get(
                    f"{self.qdrant_url}/collections/{collection['name']}"
                ).json()
                total_points += coll_info['result']['points_count']

            return {
                "collections": len(collections),
                "total_points": total_points,
                "status": "healthy"
            }
        except:
            return {"status": "error"}

    def generate_report(self):
        """Generate comprehensive health report"""
        print(f"\n🏥 Mobius Health Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # PostgreSQL
        pg_health = self.check_postgresql()
        print(f"\n📊 PostgreSQL: {pg_health['status'].upper()}")
        print(f"   Connections: {pg_health['connections']}")
        print(f"   Commits: {pg_health['commits']}")
        print(f"   Rollbacks: {pg_health['rollbacks']}")

        # Redis
        redis_health = self.check_redis()
        print(f"\n💾 Redis: {redis_health['status'].upper()}")
        print(f"   Memory: {redis_health['used_memory_mb']:.2f} MB")
        print(f"   Hit Rate: {redis_health['hit_rate']}%")
        print(f"   Clients: {redis_health['connected_clients']}")

        # Qdrant
        qdrant_health = self.check_qdrant()
        print(f"\n🔍 Qdrant: {qdrant_health['status'].upper()}")
        if qdrant_health['status'] != 'error':
            print(f"   Collections: {qdrant_health['collections']}")
            print(f"   Total Points: {qdrant_health['total_points']}")

        print("\n" + "=" * 70)

if __name__ == "__main__":
    monitor = MobiusHealthMonitor()
    monitor.generate_report()
EOF

python $TEMP_SCRIPT
rm $TEMP_SCRIPT
```

## Usage Instructions

1. **Quick Health Check**: Run the combined health dashboard script for an overview
2. **Detailed Analysis**: Use specific sections for deep dives into each database
3. **Regular Monitoring**: Set up cron jobs for periodic health checks
4. **Performance Tuning**: Use the performance metrics to identify optimization opportunities
5. **Migration Management**: Always check migration status before deployments

## Troubleshooting Common Issues

### PostgreSQL Issues
- High connection count: Check for connection leaks in application
- Low cache hit rate: Consider increasing shared_buffers
- Table bloat: Schedule regular VACUUM operations

### Qdrant Issues
- Slow searches: Check HNSW index parameters
- High memory usage: Consider sharding large collections

### Redis Issues
- Low hit rate: Review caching strategy and TTL settings
- Memory pressure: Enable eviction policies or increase memory

### Migration Issues
- Pending migrations: Run `alembic upgrade head`
- Schema drift: Review model changes and create migrations
