import pytest

from app.metrics import MetricsCollector


class TestMetricsUnit:
    @pytest.fixture(autouse=True)
    def setup_metrics(self):
        # MetricsCollector is a singleton, so we need to manually reset it for clean tests
        # This is a bit hacky but works for unit testing a singleton
        self.collector = MetricsCollector()
        with self.collector._lock:
            # Clear labeled counters
            for metric in self.collector._labeled_counters:
                self.collector._labeled_counters[metric] = {}

    def test_inc_labeled(self):
        self.collector.inc_labeled("validation_profile", "en16931")
        self.collector.inc_labeled("validation_profile", "en16931")
        self.collector.inc_labeled("validation_profile", "minimum")

        with self.collector._lock:
            assert self.collector._labeled_counters["validation_profile"]["en16931"] == 2
            assert self.collector._labeled_counters["validation_profile"]["minimum"] == 1

    def test_record_validation_all_params(self):
        error_rules = ["BR-01", "BR-02", "BR-03", "BR-04", "BR-05", "BR-06"]
        self.collector.record_validation(
            mode="teaser",
            is_valid=False,
            profile="en16931",
            error_rules=error_rules
        )

        with self.collector._lock:
            assert self.collector._labeled_counters["validation_outcome"]["teaser:invalid"] == 1
            assert self.collector._labeled_counters["validation_profile"]["en16931"] == 1
            # Should only record top 5
            assert self.collector._labeled_counters["validation_error_type"]["BR-01"] == 1
            assert self.collector._labeled_counters["validation_error_type"]["BR-05"] == 1
            assert "BR-06" not in self.collector._labeled_counters["validation_error_type"]

    def test_record_validation_minimal(self):
        self.collector.record_validation(
            mode="pro",
            is_valid=True
        )

        with self.collector._lock:
            assert self.collector._labeled_counters["validation_outcome"]["pro:valid"] == 1
            assert self.collector._labeled_counters["validation_profile"] == {}
            assert self.collector._labeled_counters["validation_error_type"] == {}
