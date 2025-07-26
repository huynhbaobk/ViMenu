import logging
import sys
import os


def setup_logging(extra_loggers: dict = None) -> None:
    """Setup application logging

    Args:
        extra_loggers (dict, optional): Logger names and levels.
            Default: {"uvicorn": INFO, "httpx": WARNING}
    """
    log_file = "logs/app.log"

    # Ensure log directory exists
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    except Exception as e:
        print(f"[Logging Setup Warning] Could not create logs dir: {e}", file=sys.stderr)

    handlers = [logging.StreamHandler(sys.stdout)]

    # Try to add FileHandler
    try:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    except PermissionError as e:
        print(f"[Logging Setup Warning] Cannot write to log file '{log_file}': {e}", file=sys.stderr)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True
    )

    # Set levels for known loggers
    if extra_loggers is None:
        extra_loggers = {
            "uvicorn": logging.INFO,
            "httpx": logging.WARNING
        }

    for logger_name, level in extra_loggers.items():
        logging.getLogger(logger_name).setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance by name"""
    return logging.getLogger(name)
