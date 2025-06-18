import signal
import logging
import logging.config
import logging.handlers
from multiprocessing import Queue
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
    startup_messages = [
        "Started server process", "Waiting for application startup",
        "Application startup complete", "Shutting down",
        "Waiting for application shutdown", "Application shutdown complete",
        "Finished server process"
    ]
    message = record.getMessage()

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
        "psyche": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level":
        "WARNING",  # Set to WARNING to silence noisy INFO logs from other libs
    }
}

def setup_logging():
  # Initialize colorama for cross-platform support
  init(autoreset=True)
  logging.config.dictConfig(LOG_CONFIG)

def log_listener_process(queue: Queue) -> None:
  """
    Listens for log records on a queue and processes them.

    This function runs in a separate process. It configures its own
    logging (using the original dictConfig) and then enters a loop
    to fetch records from the queue and handle them.
    """
  signal.signal(signal.SIGINT, signal.SIG_IGN)

  # Configure logging for this listener process
  setup_logging()
  listener_logger = logging.getLogger()

  while True:
    try:
      record = queue.get()
      if record is None:
        break
      listener_logger.handle(record)
    except Exception:
      import sys, traceback
      print('Problem in log listener:', file=sys.stderr)
      traceback.print_exc(file=sys.stderr)

def setup_worker_logging(queue: Queue) -> None:
  """
    Configures logging for a worker process to send logs to a queue.

    This should be called from the main process and any child processes.
    It removes all existing handlers and adds a single QueueHandler.
    """
  root = logging.getLogger()
  root.handlers.clear()
  root.addHandler(logging.handlers.QueueHandler(queue))
  root.setLevel(logging.INFO)
