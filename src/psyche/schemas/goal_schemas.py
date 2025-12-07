from pydantic import BaseModel, ConfigDict

class GoalRead(BaseModel):
  id: int
  title: str
  description: str | None

  model_config = ConfigDict(from_attributes=True)

class GoalCreate(BaseModel):
  title: str
  description: str | None

class GoalUpdate(BaseModel):
  title: str | None = None
  description: str | None = None
