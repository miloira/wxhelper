import os
import sys

from loguru import logger

logger.remove()
logger.add(
    sink=sys.stdout,
    format=os.environ.get("WXHELPER_LOG_FORMAT", "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>"),
    level=os.environ.get("WXHELPER_LOG_LEVEL", "DEBUG")
)
