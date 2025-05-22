import logging

"""
Module for configuring and providing a reusable logger instance.

Globals:
    - None
"""


def get_logger(name=__name__):
    """
        Returns a logger instance configured with a stream handler and standard formatter.

        Parameters:
            name (str): Name of the logger, typically passed as __name__ from the calling module.

        Returns:
            logging.Logger: A logger with level INFO and a single StreamHandler, initialized once.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
