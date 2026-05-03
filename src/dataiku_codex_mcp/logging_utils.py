"""Logging helpers for the MCP server."""

from __future__ import annotations

import logging


def get_logger(name: str = "dataiku_codex_mcp", *, debug: bool = False) -> logging.Logger:
    """Return a configured application logger."""

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.propagate = False
    return logger
