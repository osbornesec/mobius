/**
 * API Performance Monitoring
 * Tracks API call performance and timeout incidents
 */

interface ApiCallMetrics {
  endpoint: string;
  method: string;
  duration: number;
  status: 'success' | 'timeout' | 'error';
  timestamp: number;
  retryCount?: number;
}

class ApiMonitor {
  private metrics: ApiCallMetrics[] = [];
  private maxMetricsSize = 1000; // Keep last 1000 calls
  
  // Performance thresholds
  private thresholds = {
    fast: 200,     // < 200ms
    normal: 1000,  // < 1s
    slow: 5000,    // < 5s
    verySlow: 10000, // >= 10s
  };
  
  /**
   * Record an API call metric
   */
  recordMetric(metric: ApiCallMetrics): void {
    this.metrics.push(metric);
    
    // Keep metrics size under control
    if (this.metrics.length > this.maxMetricsSize) {
      this.metrics = this.metrics.slice(-this.maxMetricsSize);
    }
    
    // Log slow requests in development
    if (import.meta.env.DEV && metric.duration > this.thresholds.slow) {
      console.warn(`[API Monitor] Slow request detected:`, {
        endpoint: metric.endpoint,
        duration: `${metric.duration}ms`,
        status: metric.status,
      });
    }
  }
  
  /**
   * Get performance statistics for an endpoint
   */
  getEndpointStats(endpoint: string) {
    const endpointMetrics = this.metrics.filter(m => m.endpoint === endpoint);
    
    if (endpointMetrics.length === 0) {
      return null;
    }
    
    const durations = endpointMetrics.map(m => m.duration);
    const timeouts = endpointMetrics.filter(m => m.status === 'timeout').length;
    const errors = endpointMetrics.filter(m => m.status === 'error').length;
    
    return {
      totalCalls: endpointMetrics.length,
      avgDuration: Math.round(durations.reduce((a, b) => a + b, 0) / durations.length),
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      timeoutRate: (timeouts / endpointMetrics.length) * 100,
      errorRate: (errors / endpointMetrics.length) * 100,
      p95Duration: this.calculatePercentile(durations, 95),
      p99Duration: this.calculatePercentile(durations, 99),
    };
  }
  
  /**
   * Get overall performance summary
   */
  getPerformanceSummary() {
    const groupedBySpeed = {
      fast: 0,
      normal: 0,
      slow: 0,
      verySlow: 0,
    };
    
    this.metrics.forEach(metric => {
      if (metric.duration < this.thresholds.fast) {
        groupedBySpeed.fast++;
      } else if (metric.duration < this.thresholds.normal) {
        groupedBySpeed.normal++;
      } else if (metric.duration < this.thresholds.slow) {
        groupedBySpeed.slow++;
      } else {
        groupedBySpeed.verySlow++;
      }
    });
    
    const totalTimeouts = this.metrics.filter(m => m.status === 'timeout').length;
    const totalErrors = this.metrics.filter(m => m.status === 'error').length;
    const totalRetries = this.metrics.reduce((sum, m) => sum + (m.retryCount || 0), 0);
    
    return {
      totalCalls: this.metrics.length,
      performanceBreakdown: groupedBySpeed,
      timeoutRate: (totalTimeouts / this.metrics.length) * 100,
      errorRate: (totalErrors / this.metrics.length) * 100,
      averageRetries: totalRetries / this.metrics.length,
      slowestEndpoints: this.getSlowestEndpoints(5),
    };
  }
  
  /**
   * Get slowest endpoints
   */
  private getSlowestEndpoints(limit: number) {
    const endpointAvgs = new Map<string, { total: number; count: number }>();
    
    this.metrics.forEach(metric => {
      const key = `${metric.method} ${metric.endpoint}`;
      const current = endpointAvgs.get(key) || { total: 0, count: 0 };
      endpointAvgs.set(key, {
        total: current.total + metric.duration,
        count: current.count + 1,
      });
    });
    
    return Array.from(endpointAvgs.entries())
      .map(([endpoint, data]) => ({
        endpoint,
        avgDuration: Math.round(data.total / data.count),
        callCount: data.count,
      }))
      .sort((a, b) => b.avgDuration - a.avgDuration)
      .slice(0, limit);
  }
  
  /**
   * Calculate percentile
   */
  private calculatePercentile(values: number[], percentile: number): number {
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index];
  }
  
  /**
   * Export metrics for analysis
   */
  exportMetrics(): string {
    return JSON.stringify(this.metrics, null, 2);
  }
  
  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics = [];
  }
}

// Create singleton instance
export const apiMonitor = new ApiMonitor();

// Helper to integrate with axios
export function createMonitoringInterceptor() {
  return {
    request: (config: any) => {
      config.metadata = {
        ...config.metadata,
        startTime: Date.now(),
      };
      return config;
    },
    response: (response: any) => {
      if (response.config.metadata?.startTime) {
        const duration = Date.now() - response.config.metadata.startTime;
        apiMonitor.recordMetric({
          endpoint: response.config.url,
          method: response.config.method?.toUpperCase() || 'GET',
          duration,
          status: 'success',
          timestamp: Date.now(),
          retryCount: response.config.retryCount,
        });
      }
      return response;
    },
    error: (error: any) => {
      if (error.config?.metadata?.startTime) {
        const duration = Date.now() - error.config.metadata.startTime;
        const status = error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT' 
          ? 'timeout' 
          : 'error';
          
        apiMonitor.recordMetric({
          endpoint: error.config.url,
          method: error.config.method?.toUpperCase() || 'GET',
          duration,
          status,
          timestamp: Date.now(),
          retryCount: error.config.retryCount,
        });
      }
      return Promise.reject(error);
    },
  };
}