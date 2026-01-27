"""
Prometheus-style Metrics for Factur-X Engine.
Lightweight observability without external dependencies.
"""
import time
from threading import Lock
from typing import Dict

class MetricsCollector:
    """Thread-safe metrics collector for basic observability."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self._counters: Dict[str, int] = {
            "requests_total": 0,
            "requests_convert": 0,
            "requests_validate": 0,
            "requests_extract": 0,
            "errors_total": 0,
        }
        self._gauges: Dict[str, float] = {
            "active_requests": 0,
        }
        self._histograms: Dict[str, list] = {
            "request_duration_seconds": [],
        }
        self._start_time = time.time()
        self._lock = Lock()
    
    def inc(self, counter: str, value: int = 1):
        """Increment a counter."""
        with self._lock:
            if counter in self._counters:
                self._counters[counter] += value
    
    def set_gauge(self, gauge: str, value: float):
        """Set a gauge value."""
        with self._lock:
            if gauge in self._gauges:
                self._gauges[gauge] = value
    
    def inc_gauge(self, gauge: str, value: float = 1):
        """Increment a gauge."""
        with self._lock:
            if gauge in self._gauges:
                self._gauges[gauge] += value
    
    def dec_gauge(self, gauge: str, value: float = 1):
        """Decrement a gauge."""
        with self._lock:
            if gauge in self._gauges:
                self._gauges[gauge] -= value
    
    def observe(self, histogram: str, value: float):
        """Record an observation in a histogram."""
        with self._lock:
            if histogram in self._histograms:
                # Keep last 1000 observations
                self._histograms[histogram].append(value)
                if len(self._histograms[histogram]) > 1000:
                    self._histograms[histogram] = self._histograms[histogram][-1000:]
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # App info
        uptime = time.time() - self._start_time
        lines.append("# HELP facturx_uptime_seconds Seconds since service start")
        lines.append("# TYPE facturx_uptime_seconds gauge")
        lines.append(f"facturx_uptime_seconds {uptime:.2f}")
        lines.append("")
        
        # Counters
        lines.append("# HELP facturx_requests_total Total number of requests")
        lines.append("# TYPE facturx_requests_total counter")
        with self._lock:
            for name, value in self._counters.items():
                lines.append(f"facturx_{name} {value}")
        lines.append("")
        
        # Gauges
        lines.append("# HELP facturx_active_requests Number of requests currently being processed")
        lines.append("# TYPE facturx_active_requests gauge")
        with self._lock:
            for name, value in self._gauges.items():
                lines.append(f"facturx_{name} {value}")
        lines.append("")
        
        # Histogram summary
        with self._lock:
            durations = self._histograms.get("request_duration_seconds", [])
            if durations:
                avg = sum(durations) / len(durations)
                lines.append("# HELP facturx_request_duration_seconds_avg Average request duration")
                lines.append("# TYPE facturx_request_duration_seconds_avg gauge")
                lines.append(f"facturx_request_duration_seconds_avg {avg:.4f}")
                lines.append("")
                lines.append("# HELP facturx_request_duration_seconds_count Total observations")
                lines.append("# TYPE facturx_request_duration_seconds_count counter")
                lines.append(f"facturx_request_duration_seconds_count {len(durations)}")
        
        return "\n".join(lines)


# Singleton instance
metrics = MetricsCollector()
