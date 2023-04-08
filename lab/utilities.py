import logging
from logging import handlers
import sys


def setup_logging(log_file: str, logger = logging.getLogger()):
    """
    Setup logging to file
    """

    # clear any existing handlers
    logger.handlers.clear()

    # file handler
    file_handler = handlers.TimedRotatingFileHandler(log_file, when="D", interval=1)
    logger.addHandler(file_handler)

    # stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)
