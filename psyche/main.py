import logging
import uvicorn
from logconfig import setup_logging
from fastapi_app import app

logger = logging.getLogger("psyche")

if __name__ == "__main__":
  setup_logging()
  logger.info("Psyche Engine started")
  app.openapi_schema = None
  uvicorn.run(app, port=5010, log_config=None)
  logger.info("Psyche Engine stopped")
