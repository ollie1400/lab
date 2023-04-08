import logging
from logging import handlers
import sys


def setup_logging(log_file: str, logger = logging.getLogger()):
    """
    Setup logging to file
    """

    # clear any existing handlers
    logger.handlers.clear()

    # set format
    formatter = logging.Formatter(fmt='%(asctime)s :: %(name)s :: %(levelname)-8s :: %(message)s')

    # file handler
    file_handler = handlers.TimedRotatingFileHandler(log_file, when="D", interval=1)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # stdout handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(logging.DEBUG)
