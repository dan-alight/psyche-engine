import json
import logging
from enum import Enum
from pydantic import ValidationError
from fastapi import APIRouter, WebSocket, status, Query
from starlette.websockets import WebSocketDisconnect, WebSocketState
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update, func
from fastcrud import FastCRUD, crud_router

from psyche.database import SessionDep, get_async_session
from psyche.agent.tasks import f
from psyche.schemas.chat_schemas import (
    ConversationMessageCreate, ConversationMessageRead, ConversationRead,
    ConversationCreate, ConversationUpdate)
from psyche.models.chat_models import Conversation

logger = logging.getLogger("psyche.chat")

conversations_tags: list[str | Enum] = ["Conversations"]

conversation_crud_router = crud_router(
    session=get_async_session,
    model=Conversation,
    create_schema=ConversationCreate,
    update_schema=ConversationUpdate,
    select_schema=ConversationRead,
    path="/conversations",
    tags=conversations_tags,
    included_methods=["create", "update", "delete"])

conversation_crud = FastCRUD(Conversation)

@conversation_crud_router.get(
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
  return await conversation_crud.get_multi(
      db=db,
      offset=offset,
      limit=limit,
      sort_columns="last_updated",
      sort_orders="desc")

chat_router = APIRouter()

@chat_router.websocket("/chat")
async def chat(websocket: WebSocket):
  """WebSocket endpoint for real-time communication."""
  await websocket.accept()
  try:

    while True:
      raw_data = await websocket.receive_text()
      conversation_message_create = ConversationMessageCreate.model_validate_json(
          raw_data)
      conversation_message_read = await f(conversation_message_create)
      await websocket.send_text(conversation_message_read.model_dump_json())

  except ValidationError as e:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))

  except WebSocketDisconnect:
    pass
  except Exception as e:
    if websocket.client_state == WebSocketState.CONNECTED:
      await websocket.close(
          code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    logger.error(f"Internal error while servicing WebSocket", exc_info=True)
