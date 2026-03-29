# src/roadbook/sdk/logger.py
import logging
import sys
import os

def get_logger(name: str = "roadbook"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_level_str = os.environ.get("ROADBOOK_LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        
        logger.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
