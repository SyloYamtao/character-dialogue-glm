from loguru import logger
import os
import sys

LOG_FILE = "character_dialogue.log"
ROTATION_TIME = "02:00"


class Logger:
    def __init__(self, name="character_dialogue", log_dir="resources" + os.path.sep + "logs", debug=False):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file_path = os.path.join(log_dir, LOG_FILE)
        # Remove default loguru handler
        logger.remove()
        # Add console handler with a specific log level
        level = "DEBUG" if debug else "INFO"
        logger.add(sys.stdout, level=level)
        # Add file handler with a specific log level and timed rotation
        logger.add(log_file_path, rotation=ROTATION_TIME, level="DEBUG")
        self.logger = logger


LOG = Logger(debug=True).logger

if __name__ == "__main__":
    log = Logger().logger
