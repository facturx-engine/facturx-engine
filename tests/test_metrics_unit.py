import unittest
from collections import deque
from app.metrics import MetricsCollector

class TestMetricsCollector(unittest.TestCase):
    def test_observe_limit(self):
        collector = MetricsCollector()
        with collector._lock:
            collector._histograms["test_hist"] = deque(maxlen=1000)

        for i in range(1500):
            collector.observe("test_hist", float(i))

        durations = collector._histograms["test_hist"]
        self.assertEqual(len(durations), 1000)
        self.assertEqual(list(durations)[0], 500.0)
        self.assertEqual(list(durations)[-1], 1499.0)

    def test_prometheus_format(self):
        collector = MetricsCollector()
        collector.inc("requests_total")
        collector.observe("request_duration_seconds", 0.1)

        fmt = collector.get_basic_prometheus_format()
        self.assertIn("facturx_requests_total", fmt)
        self.assertIn("facturx_request_duration_seconds_avg", fmt)
        self.assertIn("facturx_request_duration_seconds_count", fmt)

if __name__ == "__main__":
    unittest.main()
