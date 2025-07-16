from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ConversationRead(BaseModel):
  id: int
  title: str
  last_updated: datetime | None

  model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
  title: str | None

class ConversationUpdate(BaseModel):
  title: str | None

class ConversationMessageRead(BaseModel):
  id: int
  conversation_id: int
  parent_message_id: int | None
  content: str
  role: str
  created_at: datetime

  model_config = ConfigDict(from_attributes=True)

class ConversationMessageCreate(BaseModel):
  content: str
  conversation_id: int
  parent_message_id: int | None
