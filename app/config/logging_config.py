import logging
from datetime import datetime
from logging.config import dictConfig

from app.config.settings import settings

LOG_DIR = settings.app_root / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_DATE = datetime.now().strftime("%Y-%m-%d")
LOG_FILE_NAME = f"{LOG_DATE}.jarvis-etl.{settings.app_env}.log"
LOG_FILE = LOG_DIR / LOG_FILE_NAME

def configure_logging() -> None:
	"""
	Configure global logging for the entire application.
	Includes:
			- Console logging
			- Rotating file logging
			- Module-level log format
	"""
	dictConfig(
		{
			"version": 1,
			"disable_existing_loggers": False,

			"formatters": {
				"standard": {
					"format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
				},
				"verbose": {
					"format": (
						"%(asctime)s - %(name)s - %(levelname)s - "
						"%(filename)s:%(lineno)d - %(message)s"
					),
				},
			},

			"handlers": {
				"console": {
					"class": "logging.StreamHandler",
					"formatter": "standard",
					"level": "INFO",
				},
				"file": {
					"class": "logging.handlers.RotatingFileHandler",
					"formatter": "verbose",
					"level": "DEBUG",
					"filename": str(LOG_FILE),
					"maxBytes": 5_000_000,
					"backupCount": 2,
					"encoding": "utf8",
				},
			},

			"root": {
				"handlers": ["console", "file"],
				"level": "INFO",
			},
		}
	)

	logging.getLogger(__name__).info("Logging initialized.")
