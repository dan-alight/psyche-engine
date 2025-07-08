from pydantic import BaseModel

class JournalEntryCreate(BaseModel):
  content: str

class JournalEntryRead(BaseModel):
  id: int
  content: str
  created_at: str

class JournalEntryUpdate(BaseModel):
  id: int
  content: str
