from logging import DEBUG, INFO, FileHandler, Formatter, StreamHandler, getLogger

import colorlog
from src.config import LOG_FILE_PATH

# ERROR


logger = getLogger(__name__)
logger.setLevel(INFO)

stream = StreamHandler()
stream.setLevel(INFO)
stream_format = colorlog.ColoredFormatter(
    "%(asctime)s | %(log_color)s%(levelname)-8s%(reset)s | " "%(funcName)-15s | %(message)s",
    datefmt="%H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
stream.setFormatter(stream_format)
logger.addHandler(stream)


file = FileHandler(LOG_FILE_PATH)
file.setLevel(DEBUG)
file_formatter = Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s")
file.setFormatter(file_formatter)
logger.addHandler(file)
