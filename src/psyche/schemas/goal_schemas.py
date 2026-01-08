from pydantic import BaseModel, ConfigDict

class GoalRead(BaseModel):
  id: int
  title: str
  description: str
  initial_progress: str
  strategy_guidelines: str
  active: bool

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
  active: bool | None = None

class StrategyGenerationRequest(BaseModel):
  model_id: int

class GoalStrategyRead(BaseModel):
  id: int  
  goal_id: int
  strategy: str

class GoalMetadata(BaseModel):
  goal_id: int
  has_strategy: bool