from pydantic import BaseModel, ConfigDict, Field, Json

class TaskStatus(BaseModel):
  id: int

class CancelTask(BaseModel):
  id: int
