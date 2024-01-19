from loguru import logger
import sys
import os

from config import LOG_LEVEL

"""
This file contains the custom logger.
"""

# Function to switch the logger according to the LOG_LEVEL variable
def switch_logger():
    logger.remove()
    if LOG_LEVEL in ['DEBUG', 'INFO']:
        if not os.path.exists('logs'):
            os.makedirs('logs')
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <white>{level}</white> | <level>{message}</level>"
        if LOG_LEVEL == 'DEBUG':
            log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <red>{file}</red> | <yellow>{function}</yellow> | <white>{level}</white> | <level>{message}</level>"
        logger.add(sys.stdout, level=LOG_LEVEL, colorize=True, format=log_format)
        logger.add('logs/serverbot.log', level=LOG_LEVEL, colorize=False, format=log_format)
    else:
        raise ValueError("Invalid log level")

# Call the function to set the logger according to the LOG_LEVEL variable
switch_logger()