from pydantic import BaseModel

class ChatMessageRead(BaseModel):
  id: int
  conversation_id: int
  content: str

class ChatMessageCreate(BaseModel):
  content: str
