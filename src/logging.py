import logging

def setup_logger(logger_name, log_level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [{}] %(message)s".format(logger_name), datefmt="%Y-%m-%d %H:%M:%S")
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(console_handler)
    
    return logger

# Example usage for Discord, Trakt, and Plex loggers
logger_discord = setup_logger("DISCORD")
logger_trakt = setup_logger("TRAKT")
logger_plex = setup_logger("PLEX")
logger_sonarr = setup_logger("SONARR")
logger_webhook = setup_logger("WEBHOOK")
logger_tautulli = setup_logger("TAUTULLI")