from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState
from psyche.db import AsyncSessionDep
import json
import logging

logger = logging.getLogger("psyche")

router = APIRouter()

@router.websocket("/chat")
async def chat(websocket: WebSocket, db: AsyncSessionDep):
  """WebSocket endpoint for real-time communication."""

  await websocket.accept()
  try:
    while True:
      data = await websocket.receive_text()
      message = json.loads(data)
      response = {"status": "ok", "echo": message}
      await websocket.send_text(json.dumps(response))
  except WebSocketDisconnect:
    pass
  except Exception as e:
    if websocket.client_state == WebSocketState.CONNECTED:
      await websocket.close(code=1000, reason=str(e))
    logger.warning(f"WebSocket error: {e}")
