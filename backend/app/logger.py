import sys
from pathlib import Path

from loguru import logger

# Directory for log files
log_file = Path("logs/fastapi_logs.json")
log_file.parent.mkdir(parents=True, exist_ok=True)

# Configure Loguru
logger.remove()

logger.add(
    log_file,
    rotation="50 MB",  # Rotate log after reaching 50 MB
    format="{time} {level} {message}",
    serialize=True,  # Enable JSON format
    enqueue=True,  # Async logging
    backtrace=False,
    diagnose=False,
)
logger.add(
    sys.stdout,
    format="{time} | {level} | {message} | extra: {extra}",
    enqueue=True,  # Async logging
    backtrace=False,
    diagnose=False,
)
