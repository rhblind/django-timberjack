# -*- coding: utf-8 -*-

from contextlib import ContextDecorator


class log_context(ContextDecorator):
    """
    Context manager for temporarily switching log level
    for a named logger.
    """
    def __init__(self, logger):
        self.logger = logger
        self._level = self.logger.getEffectiveLevel()

    def __enter__(self):
        return self.logger

    def __exit__(self, *exc):
        self.logger.setLevel(self._level)
