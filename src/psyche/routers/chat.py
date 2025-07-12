import json
import logging
from pydantic import ValidationError
from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect, WebSocketState

from psyche.database import SessionDep
from psyche.agent.tasks import f
from psyche.schemas.chat_schemas import ChatMessageCreate, ChatMessageRead

logger = logging.getLogger("psyche.chat")

chat_router = APIRouter()

@chat_router.websocket("/chat")
async def chat(websocket: WebSocket):
  """WebSocket endpoint for real-time communication."""

  await websocket.accept()
  try:
    while True:
      raw_data = await websocket.receive_text()
      chat_message_create = ChatMessageCreate.model_validate_json(raw_data)
      chat_message_read = await f(chat_message_create)
      await websocket.send_text(chat_message_read.model_dump_json())

  except ValidationError as e:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e))

  except WebSocketDisconnect:
    pass
  except Exception as e:
    if websocket.client_state == WebSocketState.CONNECTED:
      await websocket.close(
          code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
    logger.error(f"Internal error while servicing WebSocket", exc_info=True)
