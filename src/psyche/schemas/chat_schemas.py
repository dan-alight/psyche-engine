from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, Json
from typing import Literal, Annotated

class ConversationRead(BaseModel):
  id: int
  title: str | None
  last_updated: datetime | None

  model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
  title: str | None

class ConversationUpdate(BaseModel):
  title: str | None = None

class ConversationMessageRead(BaseModel):
  type: Literal["conversation_message_read"] = "conversation_message_read"
  id: int
  conversation_id: int
  parent_message_id: int | None
  content: str
  role: str
  created_at: datetime

  model_config = ConfigDict(from_attributes=True)

class ConversationMessageCreate(BaseModel):
  type: Literal["conversation_message_create"] = "conversation_message_create"
  content: str
  conversation_id: int
  parent_message_id: int | None

class ConversationMessagePart(BaseModel):
  type: Literal["conversation_message_part"] = "conversation_message_part"
  conversation_message_id: int
  sequence_id: int
  content: str
  final: bool

class GenerateReplyToExistingMessage(BaseModel):
  type: Literal[
      "generate_reply_to_existing_message"] = "generate_reply_to_existing_message"
  existing_message_id: int

class ChatRequest(BaseModel):
  action: Annotated[
      ConversationMessageCreate | GenerateReplyToExistingMessage,
      Field(discriminator="type"),
  ]
  config: dict = {}
