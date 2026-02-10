import pytest
import threading
from app.metrics import MetricsCollector, metrics

@pytest.fixture
def reset_metrics():
    """Reset the metrics singleton state before each test."""
    metrics._initialize()
    yield metrics

def test_singleton():
    """Verify that MetricsCollector follows the singleton pattern."""
    m1 = MetricsCollector()
    m2 = MetricsCollector()
    assert m1 is m2
    assert m1 is metrics

def test_initialization(reset_metrics):
    """Verify metrics are initialized to zero/empty."""
    m = reset_metrics

    # Check basic counters
    for counter in m._counters:
        assert m._counters[counter] == 0

    # Check gauges
    for gauge in m._gauges:
        assert m._gauges[gauge] == 0

    # Check histograms
    for hist in m._histograms:
        assert m._histograms[hist] == []

    # Check labeled counters
    for metric in m._labeled_counters:
        assert m._labeled_counters[metric] == {}

def test_increment_counter(reset_metrics):
    """Test the inc() method."""
    m = reset_metrics
    m.inc("requests_total")
    assert m._counters["requests_total"] == 1
    m.inc("requests_total", 5)
    assert m._counters["requests_total"] == 6

    # Non-existent counter should not crash
    m.inc("invalid_counter")
    assert "invalid_counter" not in m._counters

def test_gauge_operations(reset_metrics):
    """Test gauge set, inc, and dec."""
    m = reset_metrics
    m.set_gauge("active_requests", 5.5)
    assert m._gauges["active_requests"] == 5.5

    m.inc_gauge("active_requests")
    assert m._gauges["active_requests"] == 6.5

    m.inc_gauge("active_requests", 2)
    assert m._gauges["active_requests"] == 8.5

    m.dec_gauge("active_requests")
    assert m._gauges["active_requests"] == 7.5

    m.dec_gauge("active_requests", 1.5)
    assert m._gauges["active_requests"] == 6.0

def test_histogram_observations(reset_metrics):
    """Test observe() and its limit."""
    m = reset_metrics
    m.observe("request_duration_seconds", 0.1)
    m.observe("request_duration_seconds", 0.2)
    assert m._histograms["request_duration_seconds"] == [0.1, 0.2]

    # Test 1000 observations limit
    for i in range(1000):
        m.observe("request_duration_seconds", float(i))

    assert len(m._histograms["request_duration_seconds"]) == 1000
    # Should contain the last 1000 observations
    assert m._histograms["request_duration_seconds"][-1] == 999.0
    # We added 0.1, 0.2, then 0.0, 1.0, ..., 999.0 (Total 1002 elements)
    # The last 1000 elements should be 0.0, 1.0, ..., 999.0
    assert m._histograms["request_duration_seconds"][0] == 0.0

def test_labeled_counters(reset_metrics):
    """Test labeled counter increments."""
    m = reset_metrics
    m.inc_labeled("validation_outcome", "pro:valid")
    assert m._labeled_counters["validation_outcome"]["pro:valid"] == 1

    m.inc_labeled("validation_outcome", "pro:valid", 2)
    assert m._labeled_counters["validation_outcome"]["pro:valid"] == 3

    m.inc_labeled("validation_outcome", "lite:invalid")
    assert m._labeled_counters["validation_outcome"]["lite:invalid"] == 1

def test_record_validation(reset_metrics):
    """Test record_validation helper."""
    m = reset_metrics
    m.record_validation(
        mode="teaser",
        is_valid=False,
        profile="en16931",
        error_rules=["BR-01", "BR-02"],
        hidden_count=3
    )

    assert m._labeled_counters["validation_outcome"]["teaser:invalid"] == 1
    assert m._labeled_counters["validation_profile"]["en16931"] == 1
    assert m._labeled_counters["validation_error_type"]["BR-01"] == 1
    assert m._labeled_counters["validation_error_type"]["BR-02"] == 1
    assert m._labeled_counters["teaser_hidden_errors"]["2-5"] == 1

def test_prometheus_formatting(reset_metrics):
    """Test Prometheus format export."""
    m = reset_metrics
    m.inc("requests_total", 10)
    m.set_gauge("active_requests", 2)
    m.observe("request_duration_seconds", 0.5)
    m.observe("request_duration_seconds", 1.5)
    m.inc_labeled("validation_outcome", "pro:valid", 5)

    basic_format = m.get_basic_prometheus_format()
    assert "facturx_requests_total 10" in basic_format
    assert "facturx_active_requests 2" in basic_format
    assert "facturx_request_duration_seconds_avg 1.0000" in basic_format
    assert "facturx_request_duration_seconds_count 2" in basic_format
    # Labeled metrics should NOT be in basic format
    assert "validation_outcome" not in basic_format

    full_format = m.get_prometheus_format()
    assert "facturx_requests_total 10" in full_format
    assert 'facturx_validation_outcome{label="pro:valid"} 5' in full_format

def test_thread_safety(reset_metrics):
    """Verify thread safety by concurrently incrementing a counter."""
    m = reset_metrics
    num_threads = 10
    increments_per_thread = 1000

    def worker():
        for _ in range(increments_per_thread):
            m.inc("requests_total")

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert m._counters["requests_total"] == num_threads * increments_per_thread
