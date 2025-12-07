"""Centralized logging configuration for KoKoroMichi.

Provides a simple function to configure structured logging using the standard
library. Honors `LOG_LEVEL` environment variable.
"""
from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = (
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    logging.basicConfig(level=level, format=fmt)
