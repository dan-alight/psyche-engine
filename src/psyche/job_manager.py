import logging
import asyncio
from contextvars import ContextVar
from collections.abc import Awaitable, Callable
from collections import deque
from typing import Any
from psyche.schemas.job_schemas import JobRead

logger = logging.getLogger(__name__)

current_job_id: ContextVar[int] = ContextVar("current_job_id")

class JobManager:
  history_size: int = 1000
  job_queue_size: int = 100
  max_concurrent_jobs: int = 10

  def __init__(self) -> None:

    self._num_jobs = 0

    # Jobs submitted but not yet started
    self._job_queue = asyncio.Queue(maxsize=self.job_queue_size)

    # Job history
    self._job_ids_deque = deque(maxlen=self.history_size)
    self._job_read_dict: dict[int, JobRead] = {}

    self._semaphore = asyncio.Semaphore(self.max_concurrent_jobs)

  async def _job_execution_context(
      self, job_coro: Callable[[], Awaitable[Any]], job_read: JobRead) -> None:
    async with self._semaphore:
      token = current_job_id.set(job_read.id)
      try:
        await job_coro()
        job_read.status = "done"
        logger.info(f"Job {job_read.id} completed successfully.")
      except Exception as e:
        logger.exception(f"Job {job_read.id} failed with exception: {e}")
        job_read.status = "error"
        job_read.info = str(e)
      finally:
        current_job_id.reset(token)

  async def run(self) -> None:
    async with asyncio.TaskGroup() as tg:
      while True:
        job_coro, job_read = await self._job_queue.get()
        tg.create_task(self._job_execution_context(job_coro, job_read))

  def submit_job(self, job_coro: Callable[[], Awaitable[Any]]) -> JobRead:
    self._num_jobs += 1
    job_id = self._num_jobs
    job_read = JobRead(id=job_id, status="pending")

    try:
      self._job_queue.put_nowait((job_coro, job_read))

      if len(self._job_ids_deque) == self._job_ids_deque.maxlen:
        oldest_job_id = self._job_ids_deque[0]
        self._job_read_dict.pop(oldest_job_id)

      self._job_ids_deque.append(job_read.id)
      self._job_read_dict[job_read.id] = job_read

    except asyncio.QueueFull:
      job_read.status = "error"
      job_read.info = "Job queue is full."

    return job_read

  def get_job(self, job_id: int) -> JobRead | None:
    return self._job_read_dict.get(job_id)

  def get_jobs(self) -> list[JobRead]:
    return list(self._job_ids_deque)

  def get_jobs_by_ids(self, ids) -> list[JobRead]:
    return [self._job_read_dict[i] for i in ids if i in self._job_read_dict]

  def update_job(self, job_read: JobRead) -> None:
    if job_read.id in self._job_read_dict:
      self._job_read_dict[job_read.id] = job_read

job_manager = JobManager()

def get_job_manager():
  return job_manager
