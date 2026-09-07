from fastreq.utils.logging import configure_logging, reset_logging


class TestLibraryLoggingHygiene:
    """The exact production regression: importing fastreq must not let its
    loguru DEBUG chatter reach stderr via loguru's default sink."""

    def test_import_silences_rate_limiter_token_waits(self, capfd):
        import asyncio

        import fastreq  # noqa: F401 - the import IS the fix under test
        from fastreq.utils.rate_limiter import TokenBucket

        bucket = TokenBucket(requests_per_second=100, burst=10)
        bucket._tokens = 0.0  # force one wait cycle (burst=0 would deadlock: capacity 0)
        asyncio.run(bucket.acquire())

        captured = capfd.readouterr()
        assert "Rate limit: waiting" not in captured.err

    def test_explicit_enable_restores_visibility(self, capfd):
        import asyncio
        import sys

        from loguru import logger

        from fastreq.utils.rate_limiter import TokenBucket

        # self-contained sink: prior tests may have removed the default one
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        bucket = TokenBucket(requests_per_second=100, burst=10)
        bucket._tokens = 0.0
        logger.enable("fastreq")
        try:
            asyncio.run(bucket.acquire())
        finally:
            logger.remove()
            logger.disable("fastreq")

        captured = capfd.readouterr()
        assert "Rate limit: waiting" in captured.err


class TestConstructorLoggingHygiene:
    """FastRequests.__init__ must never reconfigure the host's loguru sinks."""

    def teardown_method(self):
        reset_logging()

    def test_client_construction_spares_existing_sinks(self):
        from loguru import logger

        from fastreq.client import FastRequests

        sentinel = logger.add(lambda _msg: None)  # stand-in for host app handlers
        FastRequests(backend="niquests")
        logger.remove(sentinel)  # raises ValueError if the constructor nuked it


class TestLevelParameter:
    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_info_level_shows_no_token_debug_chatter(self, capfd):
        import asyncio

        from fastreq.utils.rate_limiter import TokenBucket

        configure_logging()  # default INFO: namespace enabled, chatter filtered
        bucket = TokenBucket(requests_per_second=100, burst=10)
        bucket._tokens = 0.0  # force one wait -> logger.debug
        asyncio.run(bucket.acquire())

        assert "Rate limit: waiting" not in capfd.readouterr().err

    def test_debug_level_shows_token_debug_chatter(self, capfd):
        import asyncio

        from fastreq.utils.rate_limiter import TokenBucket

        configure_logging(level="DEBUG")
        bucket = TokenBucket(requests_per_second=100, burst=10)
        bucket._tokens = 0.0
        asyncio.run(bucket.acquire())

        assert "Rate limit: waiting" in capfd.readouterr().err

    def test_lowercase_level_accepted_and_debug_alias(self):
        assert configure_logging(level="info")[0] is False
        assert configure_logging(debug=True)[0] is True
        assert configure_logging()[0] is False


class TestConfigureLogging:
    def setup_method(self):
        reset_logging()

    def teardown_method(self):
        reset_logging()

    def test_configure_logging_default_info_level(self):
        debug, verbose = configure_logging()

        assert debug is False
        assert verbose is False

    def test_configure_logging_debug_mode(self):
        debug, verbose = configure_logging(debug=True, verbose=True)

        assert debug is True
        assert verbose is True

    def test_configure_logging_debug_false_verbose_true(self):
        debug, verbose = configure_logging(debug=False, verbose=True)

        assert debug is False
        assert verbose is True

    def test_reset_logging_no_exception(self):
        reset_logging()

    def test_configure_logging_returns_tuple(self):
        result = configure_logging()

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_configure_logging_can_be_called_multiple_times(self):
        configure_logging()
        configure_logging(debug=True)

    def test_configure_logging_debug_true_verbose_false(self):
        debug, verbose = configure_logging(debug=True, verbose=False)

        assert debug is True
        assert verbose is False
