"""Shared logging setup for runtime and API components."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Initialize process-wide logging once with a stable format."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger after ensuring baseline logging is configured."""

    if not logging.getLogger().handlers:
        configure_logging()
    return logging.getLogger(name)
