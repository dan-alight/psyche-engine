import json
import logging
from enum import Enum
from fastapi import Query
from sqlalchemy import select
from fastcrud import FastCRUD, crud_router

from psyche.database import SessionDep, get_session
from psyche.agent.tasks import f
from psyche.schemas.chat_schemas import (
    ConversationMessageRead, ConversationRead, ConversationCreate,
    ConversationUpdate)
from psyche.models.chat_models import Conversation, ConversationMessage

logger = logging.getLogger("psyche.conversations")

conversations_tags: list[str | Enum] = ["Conversations"]

conversations_crud_router = crud_router(
    session=get_session,
    model=Conversation,
    create_schema=ConversationCreate,
    update_schema=ConversationUpdate,
    select_schema=ConversationRead,
    path="/conversations",
    tags=conversations_tags,
    included_methods=["create", "update", "delete"])

conversation_crud = FastCRUD(Conversation)

@conversations_crud_router.get(
    "/conversations",
    response_model=list[ConversationRead],
    tags=conversations_tags)
async def get_conversations(
    db: SessionDep,
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(
        10, ge=1, description="Maximum number of conversations to return")):
  """
  Get a list of conversations, sorted by most recently updated.
  """
  conversations = await conversation_crud.get_multi(
      db=db,
      offset=offset,
      limit=limit,
      sort_columns="last_updated",
      sort_orders="desc")
  return conversations["data"]

@conversations_crud_router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ConversationMessageRead],
    tags=conversations_tags)
async def get_conversation_messages(db: SessionDep, conversation_id: int):
  """
    Get all messages for a specific conversation.
    """
  stmt = select(ConversationMessage).where(
      ConversationMessage.conversation_id == conversation_id)
  result = await db.execute(stmt)
  messages = result.scalars().all()
  return messages
