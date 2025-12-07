import logging
import logging.config
from colorama import Fore, Style, init

class ColorFormatter(logging.Formatter):
  COLORS = {
      'DEBUG': Fore.BLUE,
      'INFO': Fore.GREEN,
      'WARNING': Fore.YELLOW,
      'ERROR': Fore.RED,
      'CRITICAL': Fore.MAGENTA,
  }

  def format(self, record):
    color = self.COLORS.get(record.levelname, Fore.WHITE)
    original_levelname = record.levelname
    record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
    result = super().format(record)
    record.levelname = original_levelname
    return result

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "color": {
            "()": ColorFormatter,
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "plain": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "color",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "plain",
            "filename": "psyche.log",
            "mode": "a",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "aiosqlite": {
            "level": "WARNING",
            "propagate": True
        }
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG"
    }
}

def start_logging():
  init()
  logging.config.dictConfig(LOG_CONFIG)
