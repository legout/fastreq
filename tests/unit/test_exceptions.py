from fastreq.exceptions import (
    BackendError,
    ConfigurationError,
    FailureDetails,
    FastRequestsError,
    PartialFailureError,
    ProxyError,
    RateLimitExceededError,
    RetryExhaustedError,
    ValidationError,
)


class TestFastRequestsError:
    def test_base_exception_instantiation(self) -> None:
        e = FastRequestsError("connection failed")
        assert str(e) == "connection failed"
        assert isinstance(e, Exception)

    def test_base_exception_isinstance_checks(self) -> None:
        e = FastRequestsError("test")
        assert isinstance(e, FastRequestsError)
        assert isinstance(e, Exception)


class TestBackendError:
    def test_backend_error_instantiation(self) -> None:
        e = BackendError("niquests unavailable", backend_name="niquests")
        assert str(e) == "niquests unavailable"
        assert e.backend_name == "niquests"
        assert isinstance(e, FastRequestsError)
        assert isinstance(e, BackendError)

    def test_backend_error_without_name(self) -> None:
        e = BackendError("backend failed")
        assert e.backend_name is None


class TestProxyError:
    def test_proxy_error_instantiation(self) -> None:
        e = ProxyError("proxy connection failed", proxy_url="http://proxy:8080")
        assert str(e) == "proxy connection failed"
        assert e.proxy_url == "http://proxy:8080"
        assert isinstance(e, FastRequestsError)

    def test_proxy_error_without_url(self) -> None:
        e = ProxyError("proxy failed")
        assert e.proxy_url is None


class TestRetryExhaustedError:
    def test_retry_exhausted_error_attributes(self) -> None:
        timeout_err = TimeoutError("connection timeout")
        e = RetryExhaustedError(
            "failed after 3 attempts",
            attempts=3,
            last_error=timeout_err,
            url="https://example.com",
        )
        assert e.attempts == 3
        assert e.last_error is timeout_err
        assert e.url == "https://example.com"
        assert isinstance(e, FastRequestsError)


class TestRateLimitExceededError:
    def test_rate_limit_exceeded_error(self) -> None:
        e = RateLimitExceededError("rate limit exceeded", retry_after=60.0)
        assert e.retry_after == 60.0
        assert isinstance(e, FastRequestsError)


class TestValidationError:
    def test_validation_error(self) -> None:
        e = ValidationError("invalid URL", field_name="url")
        assert e.field_name == "url"
        assert isinstance(e, FastRequestsError)


class TestConfigurationError:
    def test_configuration_error(self) -> None:
        e = ConfigurationError("invalid config", config_key="backend")
        assert e.config_key == "backend"
        assert isinstance(e, FastRequestsError)


class TestFailureDetails:
    def test_failure_details_creation(self) -> None:
        err = Exception("test error")
        details = FailureDetails(url="https://example.com", error=err, attempt=2)
        assert details.url == "https://example.com"
        assert details.error is err
        assert details.attempt == 2

    def test_failure_details_default_attempt(self) -> None:
        details = FailureDetails(url="https://example.com", error=Exception())
        assert details.attempt == 0


class TestPartialFailureError:
    def test_partial_failure_error(self) -> None:
        failures = {
            "a": FailureDetails(url="https://a.com", error=Exception("a failed")),
            "b": FailureDetails(url="https://b.com", error=Exception("b failed")),
        }
        e = PartialFailureError(
            "partial failure",
            failures=failures,
            successes=8,
            total=10,
        )
        assert e.successes == 8
        assert e.total == 10
        assert len(e.failures) == 2

    def test_get_failed_urls(self) -> None:
        failures = {
            "https://a.com": FailureDetails(url="https://a.com", error=Exception()),
            "https://b.com": FailureDetails(url="https://b.com", error=Exception()),
        }
        e = PartialFailureError("partial", failures=failures)
        urls = e.get_failed_urls()
        assert "https://a.com" in urls
        assert "https://b.com" in urls

    def test_partial_failure_empty_failures(self) -> None:
        e = PartialFailureError("partial", failures=None)
        assert e.get_failed_urls() == []
