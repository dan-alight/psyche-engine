import logging
from enum import Enum
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update, func
from fastcrud import FastCRUD, crud_router
from psyche.models.ai_models import AiProvider, ApiKey, AiModel
from psyche.models.journal_models import JournalEntry
from psyche.schemas.journal_schemas import (
    JournalEntryCreate, JournalEntryUpdate, JournalEntryRead)
from psyche.database import get_session
from psyche.custom_endpoint_creator import CustomEndpointCreator
from psyche.dependencies import SessionDep

logger = logging.getLogger("psyche.journal")

tags: list[str | Enum] = ["JournalEntries"]

journal_entries_crud_router = crud_router(
    session=get_session,
    model=JournalEntry,
    create_schema=JournalEntryCreate,
    update_schema=JournalEntryUpdate,
    select_schema=JournalEntryRead,
    endpoint_creator=CustomEndpointCreator,
    path="/journal-entries",
    tags=tags,
    included_methods=["create", "read_multi", "read", "delete", "update"],
)

journal_entries_router = APIRouter()

@journal_entries_router.get("/journal-entries/stats", tags=tags)
async def get_journal_entries_stats(db: SessionDep):
  stmt = select(func.count()).select_from(JournalEntry)
  result = await db.execute(stmt)
  count = result.scalar_one()
  return {"count": count}
