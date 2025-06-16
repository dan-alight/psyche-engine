from enum import Enum
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update, func
from fastcrud import FastCRUD, crud_router
from psyche.db import AsyncSessionDep, ApiKey, JournalEntry, get_async_session

# --- Pydantic Models ---

class JournalEntryCreate(BaseModel):
  content: str

class JournalEntryRead(BaseModel):
  id: int
  content: str
  created_at: str

class JournalEntryUpdate(BaseModel):
  id: int
  content: str

# --- Routes ---

tags: list[str | Enum] = ["JournalEntries"]

router = crud_router(
    session=get_async_session,
    model=JournalEntry,
    create_schema=JournalEntryCreate,
    update_schema=JournalEntryUpdate,
    path="/journal-entries",
    tags=tags,
    included_methods=["create", "read", "read_multi", "delete"])

stats_router = APIRouter()

@stats_router.get("/journal-entries/stats", tags=tags)
async def get_journal_entries_stats(db: AsyncSessionDep):
  stmt = select(func.count()).select_from(JournalEntry)
  result = await db.execute(stmt)
  count = result.scalar_one()
  return {"count": count}
