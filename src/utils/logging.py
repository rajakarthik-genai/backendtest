"""
Central logging configuration used across the backend.

• INFO level by default
• DEBUG if settings.debug is True
"""

import logging, sys
from src.config.settings import settings

_level = logging.DEBUG if settings.debug else logging.INFO

logging.basicConfig(
    level=_level,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("meditwin")
logger.info("Logging initialised (level=%s)", logging.getLevelName(_level))
