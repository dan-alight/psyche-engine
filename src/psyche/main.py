import asyncio
import uvicorn
from psyche.fastapi_app import app
from psyche.log_config import start_logging
from psyche.database import run_migrations

WEBSERVER_PORT = 8000

async def main():
  start_logging()
  run_migrations()
  config = uvicorn.Config(app, port=WEBSERVER_PORT, log_config=None)
  server = uvicorn.Server(config)
  try:
    async with asyncio.TaskGroup() as tg:
      tg.create_task(server.serve())
  except asyncio.CancelledError:
    pass

if __name__ == "__main__":
  asyncio.run(main())
