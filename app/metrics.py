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
        # === BASIC METRICS (Community) ===
        self._counters: Dict[str, int] = {
            "requests_total": 0,
            "requests_convert": 0,
            "requests_validate": 0,
            "requests_extract": 0,
            "requests_xml": 0,
            "errors_total": 0,
        }
        self._gauges: Dict[str, float] = {
            "active_requests": 0,
        }
        self._histograms: Dict[str, list] = {
            "request_duration_seconds": [],
        }
        
        # === PRO-TIER BUSINESS METRICS ===
        # Validation outcomes by mode
        self._labeled_counters: Dict[str, Dict[str, int]] = {
            # validation_outcome{mode="pro|teaser|lite", result="valid|invalid"}
            "validation_outcome": {},
            # validation_profile{profile="minimum|basicwl|basic|en16931|extended"}
            "validation_profile": {},
            # validation_error_type{rule_id="BR-01|BR-CO-17|..."}
            "validation_error_type": {},
            # teaser_errors_hidden (histogram of how many errors we hide per request)
            "teaser_hidden_errors": {},
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
    
    # === PRO-TIER METHODS ===
    
    def inc_labeled(self, metric: str, label: str, value: int = 1):
        """Increment a labeled counter (Pro feature)."""
        with self._lock:
            if metric in self._labeled_counters:
                if label not in self._labeled_counters[metric]:
                    self._labeled_counters[metric][label] = 0
                self._labeled_counters[metric][label] += value
    
    def record_validation(self, mode: str, is_valid: bool, profile: str = None, 
                          error_rules: list = None, hidden_count: int = 0):
        """
        Record a validation event with business metrics (Pro feature).
        
        Args:
            mode: "pro", "teaser", or "lite"
            is_valid: Whether validation passed
            profile: Detected Factur-X profile (en16931, minimum, etc.)
            error_rules: List of rule IDs that failed (e.g., ["BR-CO-17", "BR-01"])
            hidden_count: Number of errors hidden in teaser mode
        """
        # Outcome by mode
        result = "valid" if is_valid else "invalid"
        self.inc_labeled("validation_outcome", f"{mode}:{result}")
        
        # Profile detection
        if profile:
            self.inc_labeled("validation_profile", profile)
        
        # Error type breakdown (top errors for dashboard)
        if error_rules:
            for rule_id in error_rules[:5]:  # Top 5 errors per request
                self.inc_labeled("validation_error_type", rule_id)
        
        # Teaser conversion opportunity tracking
        if mode == "teaser" and hidden_count > 0:
            bucket = "1" if hidden_count == 1 else "2-5" if hidden_count <= 5 else "6+"
            self.inc_labeled("teaser_hidden_errors", bucket)
    
    def get_basic_prometheus_format(self) -> str:
        """Export BASIC metrics only (Community tier)."""
        lines = []
        
        # App info
        uptime = time.time() - self._start_time
        lines.append("# HELP facturx_uptime_seconds Seconds since service start")
        lines.append("# TYPE facturx_uptime_seconds gauge")
        lines.append(f"facturx_uptime_seconds {uptime:.2f}")
        lines.append("")
        
        # Counters (basic)
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
        
        # Histogram summary (without labels)
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
    
    def get_prometheus_format(self) -> str:
        """Export ALL metrics including Pro-tier business metrics."""
        # Start with basic metrics
        lines = [self.get_basic_prometheus_format()]
        
        # === PRO-TIER LABELED METRICS ===
        with self._lock:
            for metric_name, labels in self._labeled_counters.items():
                if labels:
                    lines.append("")
                    lines.append(f"# HELP facturx_{metric_name} Business metric with labels (Pro)")
                    lines.append(f"# TYPE facturx_{metric_name} counter")
                    for label, value in labels.items():
                        lines.append(f'facturx_{metric_name}{{label="{label}"}} {value}')
        
        return "\n".join(lines)


# Singleton instance
metrics = MetricsCollector()
