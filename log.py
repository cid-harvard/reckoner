__all__ = ["INFO", "WARNING", "ERROR", "log"]
import os.path

import logging
from logging import INFO, WARNING, ERROR, DEBUG

logging.basicConfig(
    format='%(levelname)s:  %(message)s',
    level=logging.INFO)
logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" %
                     logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" %
                     logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" %
                     logging.getLevelName(logging.ERROR))


def log(level, message, *args, **kwargs):
    """Same as the python logging command, except prefixes by
    file_being_processed if given."""

    if "file_being_processed" in kwargs:
        message = "{file_name}: {message}".format(
            file_name=os.path.basename(kwargs["file_being_processed"]),
            message=message)
    return logging.log(level, message, *args, **kwargs)
