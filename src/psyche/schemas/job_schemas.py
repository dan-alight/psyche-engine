from pydantic import BaseModel
from typing import Literal

JobStatus = Literal["pending", "done", "error"]

class JobRead(BaseModel):
  id: int
  status: JobStatus
  info: str | None = None

class JobBatchRequest(BaseModel):
  job_ids: list[int]
