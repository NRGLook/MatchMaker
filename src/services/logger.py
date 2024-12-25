import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter, Logger, StreamHandler
import os
from src.config.app_config import settings


class LoggerProvider:
    """
    Helper class for getting a logger.
    Applies basic settings to the built-in logger and
    returns a logger instance with the specified name.
    """

    def __init__(self):
        if not os.path.exists("./logs"):
            os.mkdir("./logs")
        self.handler = TimedRotatingFileHandler(
            settings.LOG_FILE_PATH, "D", 1, 3, "utf-8")
        linear_formatter = Formatter(
            "%(asctime)s: %(levelname)s [%(threadName)s]"
            " %(funcName)s(%(lineno)d): %(message)s", "%Y-%m-%d %H:%M:%S")
        self.handler.setFormatter(linear_formatter)

        self.console_handler = StreamHandler()
        self.console_handler.setFormatter(linear_formatter)

    def get_logger(self, name: str) -> Logger:
        logger = Logger(name)
        logger.setLevel(logging.INFO)
        if self.handler not in logger.handlers:
            logger.addHandler(self.handler)
        if self.console_handler not in logger.handlers:
            logger.addHandler(self.console_handler)

        return logger


def tail(file_path: str, lines: int) -> list:
    """
    Returns the last lines from the file.
    :param file_path: Path to the file.
    :param lines: Number of lines to get from the end of the file.
    :return: List of lines from the file.
    """
    with open(file_path, "rb") as file:
        file.seek(0, os.SEEK_END)
        buffer = bytearray()
        pointer_location = file.tell()

        while pointer_location >= 0 and lines > 0:
            file.seek(pointer_location)
            pointer_location -= 1
            new_byte = file.read(1)

            if new_byte == b'\n' and buffer:
                lines -= 1
                if lines == 0:
                    break

            buffer.extend(new_byte)

        if not buffer:
            return []

        return buffer.decode('utf-8', errors='ignore')[::-1].splitlines()[::-1]
