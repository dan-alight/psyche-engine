from datetime import datetime
from pydantic import BaseModel

class JournalEntryCreate(BaseModel):
  content: str

class JournalEntryRead(BaseModel):
  id: int
  content: str
  created_at: datetime
  version: int

class JournalEntryUpdate(BaseModel):
  content: str | None = None
