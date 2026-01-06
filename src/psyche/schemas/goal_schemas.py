from pydantic import BaseModel, ConfigDict

class GoalRead(BaseModel):
  id: int
  title: str
  description: str
  initial_progress: str
  strategy_guidelines: str

  model_config = ConfigDict(from_attributes=True)

class GoalCreate(BaseModel):
  title: str
  description: str
  initial_progress: str
  strategy_guidelines: str

class GoalUpdate(BaseModel):
  title: str | None = None
  description: str | None = None
  initial_progress: str | None = None
  strategy_guidelines: str | None = None

class StrategyGenerationRequest(BaseModel):
  model_id: int
