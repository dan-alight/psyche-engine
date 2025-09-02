import logging
import asyncio
import uvicorn

from psyche.logconfig import setup_logging
from psyche.database import upgrade_database
from psyche.fastapi_app import app
from psyche.task_executor import TaskExecutor

_WEBSERVER_PORT = 5010
logger = logging.getLogger("psyche")

async def main():
  setup_logging()
  upgrade_database()

  config = uvicorn.Config(
      app,
      port=_WEBSERVER_PORT,
      log_config=None,
  )
  server = uvicorn.Server(config)

  task_executor = TaskExecutor()
  app.state.executor = task_executor

  try:
    async with asyncio.TaskGroup() as tg:
      tg.create_task(server.serve())
      tg.create_task(task_executor.run())
  except asyncio.CancelledError:
    pass
  finally:
    logger.info("Psyche shutting down.")

if __name__ == "__main__":
  asyncio.run(main())
