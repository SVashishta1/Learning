# safe_logging.py: logs that can't leak personal data, even when a developer logs the wrong thing.
#
# Logs get copied everywhere: log servers, support tickets, screenshots, AI tracing tools. So the rule is:
# log ids and counts, not content. And as a safety net, mask anything that slips through.
import logging

import pii


class RedactingFilter(logging.Filter):
    """A logging filter runs on every log record before it is written. This one masks PII in the message."""

    def filter(self, record):
        message = record.getMessage()                 # the final text, with any %s arguments filled in
        record.msg, record.args = pii.mask(message), None
        return True                                   # True = still write the (now masked) record


def get_logger(name="northwind", stream=None):
    logger = logging.getLogger(name)
    if not logger.handlers:                           # don't add a second handler if called twice
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False                      # don't also pass records to other (unfiltered) loggers
    return logger
