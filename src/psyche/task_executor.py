from typing import Callable, Coroutine, Any, Tuple
import logging
import asyncio

logger = logging.getLogger("psyche.executor")

class TaskExecutor():
  """
  An asynchronous task executor using asyncio.
  """

  def __init__(self, task_buffer_size: int = 100):
    self._task_queue: asyncio.Queue = asyncio.Queue(maxsize=task_buffer_size)

  async def submit_task(
      self, task_callable: Callable[..., Coroutine], *args: Any,
      **kwargs: Any) -> None:
    task_package = (task_callable, args, kwargs)
    await self._task_queue.put(task_package)

  async def _task_wrapper(
      self, task_callable: Callable[..., Coroutine], args: Tuple, kwargs: dict):
    """
    A wrapper that executes the task and logs any exceptions.
    """
    logger.info(f"Executing task: {task_callable.__name__}")
    try:
      await task_callable(*args, **kwargs)
    except Exception:
      logger.exception(f"Exception in task {task_callable.__name__}")
    finally:
      logger.info(f"Finished task: {task_callable.__name__}")

  async def run(self):
    """
    Starts the executor's task manager and runs until it's cancelled.
    """
    logger.info("Executor started")
    try:
      async with asyncio.TaskGroup() as tg:
        while True:
          task_callable, args, kwargs = await self._task_queue.get()

          tg.create_task(self._task_wrapper(task_callable, args, kwargs))
    finally:
      logger.info("Executor shutting down")
