import time
import logging
import multiprocessing
from psyche.logconfig import setup_worker_logging, log_listener_process, setup_logging
from psyche.db import run_alembic_upgrade

if __name__ == "__main__":
  # Prevent pointless re-import on child process spawn
  import uvicorn
  from psyche.fastapi_app import app

  log_queue = multiprocessing.Queue()
  listener_process = multiprocessing.Process(
      target=log_listener_process, args=(log_queue, ))
  listener_process.start()

  setup_worker_logging(log_queue)

  logger = logging.getLogger("psyche")

  run_alembic_upgrade()

  try:
    uvicorn.run(app, port=5010, log_config=None)
  finally:
    log_queue.put(None)
    listener_process.join()

  setup_logging()
  final_logger = logging.getLogger("psyche")
  final_logger.info("Program shutting down")
