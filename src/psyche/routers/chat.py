import logging
from pydantic import ValidationError
from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect, WebSocketState
from psyche.database import SessionLocal
from psyche.agent.tasks import f
from psyche.schemas.chat_schemas import (
    ConversationMessageCreate, ConversationMessageRead)
from psyche.models.chat_models import ConversationMessage, ConversationMessageRole

logger = logging.getLogger("psyche.chat")

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

      async with SessionLocal() as db:
        async with db.begin():
          db_message = ConversationMessage(
              **conversation_message_create.model_dump(),
              role=ConversationMessageRole.USER,
          )
          db.add(db_message)
        await db.refresh(db_message)

      message_response = ConversationMessageRead.model_validate(db_message)
      await websocket.send_json(message_response.model_dump(mode='json'))

      # Produce response and stream parts back

  except ValidationError as e:
    logger.error(str(e))
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

  except WebSocketDisconnect:
    pass

  except Exception as e:
    if websocket.client_state == WebSocketState.CONNECTED:
      await websocket.close(
          code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    logger.error(f"Internal error while servicing WebSocket", exc_info=True)
