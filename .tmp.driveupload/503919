"""
Unit tests for monitoring.py - CloudWatch metrics module.
Tests metric publishing, helpers, and decorators.
"""


from unittest.mock import patch, MagicMock
import time


class TestPublishMetric:
    """Tests for publish_metric function."""

    def test_publish_metric_calls_cloudwatch(self):
        """Test that metric is published to CloudWatch."""
        import monitoring

        mock_cw = MagicMock()

        with patch.object(monitoring, "get_cloudwatch") as mock_get_cw:
            with patch.object(monitoring, "POWERTOOLS_AVAILABLE", False):
                mock_get_cw.return_value = mock_cw

                monitoring.publish_metric("TestMetric", 1.0, "Count")

                mock_cw.put_metric_data.assert_called_once()

    def test_publish_metric_includes_dimensions(self):
        """Test that standard dimensions are included."""
        import monitoring

        mock_cw = MagicMock()

        with patch.object(monitoring, "get_cloudwatch") as mock_get_cw:
            with patch.object(monitoring, "POWERTOOLS_AVAILABLE", False):
                mock_get_cw.return_value = mock_cw

                monitoring.publish_metric(
                    "TestMetric", 1.0, "Count",
                    dimensions={"Custom": "value"}
                )

                call_args = mock_cw.put_metric_data.call_args
                metric_data = call_args[1]["MetricData"][0]
                dim_names = [d["Name"] for d in metric_data["Dimensions"]]

                assert "Environment" in dim_names
                assert "Service" in dim_names
                assert "Custom" in dim_names


class TestPublishHelpers:
    """Tests for metric publishing helper functions."""

    def test_publish_latency_uses_milliseconds(self):
        """Test that latency is published in milliseconds."""
        import monitoring

        with patch.object(monitoring, "publish_metric") as mock_publish:
            monitoring.publish_latency("TestLatency", 150.5)

            mock_publish.assert_called_once_with(
                "TestLatency", 150.5, "Milliseconds", None
            )

    def test_publish_count_uses_count_unit(self):
        """Test that count uses Count unit."""
        import monitoring

        with patch.object(monitoring, "publish_metric") as mock_publish:
            monitoring.publish_count("TestCount", 5)

            mock_publish.assert_called_once_with(
                "TestCount", 5.0, "Count", None
            )

    def test_publish_error_adds_error_type_dimension(self):
        """Test that error metrics include error type."""
        import monitoring

        with patch.object(monitoring, "publish_count") as mock_count:
            monitoring.publish_error("TestError", "ValueError")

            # Check dimensions in positional arguments (args[2])
            call_args = mock_count.call_args
            dimensions = call_args[0][2]
            assert dimensions["ErrorType"] == "ValueError"


class TestMeasureLatency:
    """Tests for measure_latency context manager."""

    def test_measure_latency_publishes_duration(self):
        """Test that latency is measured and published."""
        import monitoring

        with patch.object(monitoring, "publish_latency") as mock_publish:
            with monitoring.measure_latency("TestLatency"):
                time.sleep(0.01)  # 10ms

            mock_publish.assert_called_once()
            duration = mock_publish.call_args[0][1]
            assert duration >= 10  # At least 10ms


class TestRecordChatRequest:
    """Tests for record_chat_request helper."""

    def test_record_chat_request_publishes_metrics(self):
        """Test that chat request metrics are published."""
        import monitoring

        with patch.object(monitoring, "publish_count") as mock_count:
            with patch.object(monitoring, "publish_latency") as mock_latency:
                monitoring.record_chat_request(
                    is_authenticated=True,
                    has_images=True,
                    language="English",
                    latency_ms=1500.0
                )

                # Should publish multiple count metrics
                assert mock_count.call_count >= 2
                # Should publish latency
                mock_latency.assert_called_once()


class TestRecordLlmCall:
    """Tests for record_llm_call helper."""

    def test_record_llm_call_publishes_all_metrics(self):
        """Test that LLM call metrics are published."""
        import monitoring

        with patch.object(monitoring, "publish_count") as mock_count:
            with patch.object(monitoring, "publish_latency") as mock_latency:
                with patch.object(monitoring, "publish_metric") as mock_metric:
                    monitoring.record_llm_call(
                        model="gemini-2.5-pro",
                        latency_ms=2500.0,
                        input_tokens=100,
                        output_tokens=500,
                        success=True
                    )

                    # Should publish request count and latency
                    assert mock_count.call_count >= 1
                    mock_latency.assert_called_once()
                    # Should publish token metrics
                    assert mock_metric.call_count >= 2


class TestRecordSecurityEvent:
    """Tests for record_security_event helper."""

    def test_record_auth_failure(self):
        """Test recording auth failure event."""
        import monitoring

        with patch.object(monitoring, "publish_count") as mock_count:
            monitoring.record_security_event("auth_failure")

            mock_count.assert_called()
            call_args = mock_count.call_args
            assert call_args[0][0] == monitoring.MetricName.AUTH_FAILURES

    def test_record_rate_limit(self):
        """Test recording rate limit event."""
        import monitoring

        with patch.object(monitoring, "publish_count") as mock_count:
            monitoring.record_security_event("rate_limit")

            mock_count.assert_called()
            call_args = mock_count.call_args
            assert call_args[0][0] == monitoring.MetricName.RATE_LIMIT_HITS


class TestMetricNames:
    """Tests for MetricName constants."""

    def test_metric_names_defined(self):
        """Test that required metric names are defined."""
        import monitoring

        assert hasattr(monitoring.MetricName, "API_REQUESTS")
        assert hasattr(monitoring.MetricName, "CHAT_REQUESTS")
        assert hasattr(monitoring.MetricName, "LLM_REQUESTS")
        assert hasattr(monitoring.MetricName, "LLM_ERRORS")
        assert hasattr(monitoring.MetricName, "GUEST_TRIAL_LIMIT")
