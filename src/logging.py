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
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"logs/infos_{datetime.now():%Y-%m-%d}.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "discord": {
            "handlers": ["console2", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "sonarr": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "radarr": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "tautulli": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "trakt": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "plex": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)