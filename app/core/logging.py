import logging
import sys
import os


def setup_logging(
    extra_loggers: dict = None
) -> None:
    """Setup application logging

    Args:
        extra_loggers (dict, optional): Dictionary of logger names and their levels.
            Example: {"uvicorn": logging.INFO, "httpx": logging.WARNING}
            By default, sets 'uvicorn' to INFO and 'httpx' to WARNING.
    """
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log", encoding="utf-8")
        ],
        force=True
    )
    # Set specific loggers
    if extra_loggers is None:
        extra_loggers = {
            "uvicorn": logging.INFO,
            "httpx": logging.WARNING
        }
    for logger_name, level in extra_loggers.items():
        logging.getLogger(logger_name).setLevel(level)
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)