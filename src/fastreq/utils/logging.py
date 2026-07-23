import sys

from loguru import logger


def configure_logging(debug: bool = False, verbose: bool = False) -> tuple[bool, bool]:
    """Configure loguru logging with appropriate level based on debug/verbose flags.

    Args:
        debug: Enable DEBUG level logging if True, INFO level if False
        verbose: Controls tqdm progress bar visibility (returned for caller use)

    Returns:
        Tuple of (debug_enabled, verbose_enabled) for progress bar control
    """
    logger.remove()

    log_level = "DEBUG" if debug else "INFO"

    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>"
    )

    logger.add(
        sink=sys.stderr,
        level=log_level,
        format=format_string,
        colorize=True,
    )

    return debug, verbose


def reset_logging() -> None:
    """Remove all loguru handlers to allow clean reconfiguration."""
    logger.remove()
