from fastreq.utils.logging import configure_logging, reset_logging


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
