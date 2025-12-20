"""
Unit tests for utility modules.

Tests logging and retry utilities.
"""


import pytest

from app.utils.logger import get_logger
from app.utils.retry import retry_with_backoff


class TestLogger:
    """Tests for logger utility."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        logger = get_logger(__name__)
        assert logger is not None

    def test_logger_has_standard_methods(self) -> None:
        """Test that logger has standard logging methods."""
        logger = get_logger(__name__)
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "debug")


class TestRetry:
    """Tests for retry utility."""

    def test_retry_succeeds_on_first_attempt(self) -> None:
        """Test that successful function doesn't retry."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        def successful_function() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_retries_on_failure(self) -> None:
        """Test that function retries on exception."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, min_wait=0, max_wait=0)
        def failing_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_raises_after_max_attempts(self) -> None:
        """Test that retry gives up after max attempts."""

        @retry_with_backoff(max_attempts=2, min_wait=0, max_wait=0)
        def always_failing_function() -> str:
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            always_failing_function()

    def test_retry_only_catches_specified_exceptions(self) -> None:
        """Test that retry only catches specified exception types."""

        @retry_with_backoff(max_attempts=3, exceptions=(ValueError,), min_wait=0, max_wait=0)
        def function_with_wrong_exception() -> str:
            raise TypeError("Wrong exception type")

        # Should not retry on TypeError
        with pytest.raises(TypeError):
            function_with_wrong_exception()
