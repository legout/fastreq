import sys

from loguru import logger


def configure_logging(
    level: str = "INFO",
    verbose: bool = False,
    *,
    debug: bool | None = None,
) -> tuple[bool, bool]:
    """Configure a stderr sink at the given level and enable the fastreq namespace.

    Calling this helper is the explicit opt-in: importing fastreq leaves
    its namespace disabled (library pattern), so nothing from fastreq
    reaches stderr until an app configures it here.

    Args:
        level: Minimum level for the stderr sink ("INFO" shows operational
            lines like backend selection and retry exhaustion without the
            per-request/per-token DEBUG chatter; "DEBUG" shows everything).
        verbose: Controls tqdm progress bar visibility (returned for caller use).
        debug: Deprecated boolean alias: ``True`` == ``level="DEBUG"``.
            Kept for backwards compatibility.

    Returns:
        Tuple of (debug_enabled, verbose_enabled) for progress bar control;
        ``debug_enabled`` is ``level == "DEBUG"``.
    """
    if debug is not None:
        level = "DEBUG" if debug else "INFO"
    level = level.upper()

    logger.remove()
    logger.enable("fastreq")

    format_string = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{message}</cyan>"
    )

    logger.add(
        sink=sys.stderr,
        level=level,
        format=format_string,
        colorize=True,
    )

    return level == "DEBUG", verbose


def reset_logging() -> None:
    """Remove all loguru handlers and restore the import-time default (namespace disabled)."""
    logger.remove()
    logger.disable("fastreq")
