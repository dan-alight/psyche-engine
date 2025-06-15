from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update
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

router = crud_router(
    session=get_async_session,
    model=JournalEntry,
    create_schema=JournalEntryCreate,
    update_schema=JournalEntryUpdate,
    path="/journal-entries",
    tags=["JournalEntries"],
    included_methods=["create", "read_multi", "delete"])
