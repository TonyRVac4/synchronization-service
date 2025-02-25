from loguru import logger
from config import LOG_FILE_PATH
logger.remove()

logger.add(
    LOG_FILE_PATH,
    level="INFO",
    rotation="10 MB",
    compression="zip",
    format="synchronizer {time:YYYY-MM-DDD HH:mm:ss} {level} {message}"
)
