from pydantic import BaseModel
from typing import Literal

JobStatus = Literal["pending", "completed", "failed"]

class JobRead(BaseModel):
  id: int
  status: JobStatus
  info: str | None = None
