from datetime import datetime
from pydantic import BaseModel

class JournalEntryCreate(BaseModel):
  content: str

class JournalEntryRead(BaseModel):
  id: int
  content: str
  created_at: datetime
  last_edited: datetime | None

class JournalEntryUpdate(BaseModel):
  content: str | None = None
