"""
Central logging setup. Import and call configure_logging() once at the
start of any entrypoint (app.py, a future CLI, a future API) instead of
scattering print() calls through the business logic -- that's what let
extractor.py and matcher.py stay silent-by-default and testable.
"""
import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
