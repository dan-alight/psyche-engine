import logging
import logging.config
from colorama import Fore, Style, init

class CustomColoredFormatter(logging.Formatter):
  """Custom formatter to add colors to log levels"""

  # Define colors for each log level
  COLORS = {
      'DEBUG': Fore.CYAN,
      'INFO': Fore.GREEN,
      'WARNING': Fore.YELLOW,
      'ERROR': Fore.RED,
      'CRITICAL': Fore.RED + Style.BRIGHT,
  }

  def __init__(self, fmt=None, datefmt=None, use_colors=True):
    super().__init__(fmt, datefmt)
    self.use_colors = use_colors

  def format(self, record):
    # Get the original formatted message
    log_message = super().format(record)

    # Add color based on log level (only if use_colors is True)
    if self.use_colors:
      color = self.COLORS.get(record.levelname, '')
      if color:
        # Color the entire level name (INFO, WARNING, ERROR, etc.)
        colored_level = f"{color}{record.levelname}{Style.RESET_ALL}"
        log_message = log_message.replace(record.levelname, colored_level, 1)

    return log_message

class UvicornFilter(logging.Filter):
  """Filter to hide uvicorn startup/shutdown messages but keep WebSocket logs"""

  def filter(self, record) -> bool:
    # Messages to filter out
    startup_messages = [
        "Started server process", "Waiting for application startup",
        "Application startup complete", "Shutting down",
        "Waiting for application shutdown", "Application shutdown complete",
        "Finished server process"
    ]
    message = record.getMessage()

    # Return False to filter out, True to keep
    return not any(startup_msg in message for startup_msg in startup_messages)

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console_color": {
            "()": CustomColoredFormatter,
            "fmt": "[%(asctime)s] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": True,
        },
        "file_plain": {
            "()": CustomColoredFormatter,
            "fmt": "[%(asctime)s] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "use_colors": False,
        },
    },
    "filters": {
        "uvicorn_filter": {
            "()": UvicornFilter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console_color",
            "stream": "ext://sys.stdout",
            "filters": ["uvicorn_filter"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file_plain",
            "filename": "app.log",
            "maxBytes": 5_000_000,
            "backupCount": 5,
        },
    },
    "loggers": {
        # Your application's logger
        "psyche": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn's access logger
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        # Uvicorn's error logger
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    # NEW: Configure the root logger to catch asyncio and other library logs
    "root": {
        "handlers": ["console", "file"],
        "level":
        "WARNING",  # Set to WARNING to silence noisy INFO logs from other libs
    }
}

# Set up logging with the configuration
def setup_logging():
  # Initialize colorama for cross-platform support
  init(autoreset=True)
  logging.config.dictConfig(LOG_CONFIG)
