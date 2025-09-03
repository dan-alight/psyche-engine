import logging
import asyncio
from pydantic import ValidationError
from fastapi import APIRouter, WebSocket, status
from starlette.websockets import WebSocketDisconnect, WebSocketState
from sqlalchemy.inspection import inspect
from psyche.database import SessionLocal
from psyche.agents.tasks import stream_chat
from psyche.schemas.chat_schemas import ChatRequest
from psyche.schemas.generic_schemas import TaskStatus, CancelTask
from psyche.models.chat_models import ConversationMessage, ConversationMessageRole
from psyche.exceptions import InvalidStateError

logger = logging.getLogger("psyche.chat")
active_chat_tasks: dict[int, asyncio.Task] = {}

chat_router = APIRouter()

@chat_router.post("/chat/cancel")
async def cancel_chat_generation(cancel_task: CancelTask):
  """Cancel a running chat generation task."""
  task = active_chat_tasks.get(cancel_task.id)

  if not task:
    raise InvalidStateError(f"No active task found with ID {cancel_task.id}")

  if task.done():
    return {"status": "Task was already completed."}

  task.cancel()

  logger.info(f"Cancellation requested for task: {cancel_task.id}")
  return {"status": "cancellation_requested"}

@chat_router.websocket("/chat")
async def chat(websocket: WebSocket):
  """WebSocket endpoint for real-time communication."""

  await websocket.accept()

  async for message in websocket.iter_text():
    chat_request = ChatRequest.model_validate_json(message)

    async def stream_and_send():
      try:
        async for chunk in stream_chat(chat_request):
          # Send each chunk to the client as it becomes available
          await websocket.send_json(chunk)
      except asyncio.CancelledError:
        logger.info("Streaming task was cancelled.")

    # Create a task to run the streaming process in the background.
    task = asyncio.create_task(stream_and_send())

    # Store the task so the /cancel endpoint can find it.
    task_id = websocket.app.state.tasks_started
    active_chat_tasks[task_id] = task
    websocket.app.state.tasks_started += 1

    # Return the TaskStatus
    await websocket.send_json(TaskStatus(id=task_id).model_dump(mode="json"))

    try:
      await task
    finally:
      del active_chat_tasks[task_id]
