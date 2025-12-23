from datetime import date as datetime_date
from pydantic import BaseModel, ConfigDict

class ActivityRead(BaseModel):
  id: int
  description: str
  date: datetime_date
  completed: bool

  model_config = ConfigDict(from_attributes=True)

class ActivityCreate(BaseModel):
  description: str
  date: datetime_date

class ActivityUpdate(BaseModel):
  completed: bool | None = None

class CalendarGenerationRequest(BaseModel):
  pass
