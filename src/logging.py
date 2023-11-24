import logging
from logging.config import dictConfig

from datetime import datetime

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"logs/infos_{datetime.now():%Y-%m-%d}.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console", "file"], 
            "level": "INFO", 
            "propagate": False
        },
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "sonarr": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "radarr": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "tautulli": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "trakt": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "plex": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)