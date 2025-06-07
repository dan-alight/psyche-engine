import json
from contextlib import asynccontextmanager
import logging
import time

import uvicorn
from fastapi import FastAPI, WebSocket, Request
from starlette.websockets import WebSocketDisconnect, WebSocketState
from db import create_db_and_tables
from uvicorn.logging import DefaultFormatter
from logging.handlers import RotatingFileHandler
from logconfig import setup_logging

setup_logging()
logger = logging.getLogger("psyche")

# --- Pydantic Models for API Validation ---

# --- FastAPI Application (runs in the main process) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
  """A simple root endpoint."""
  return {"message": "Welcome to the Async AI Inference Service!"}

@app.websocket("/chat")
async def chat(websocket: WebSocket):
  """WebSocket endpoint for real-time communication."""
  await websocket.accept()
  try:
    while True:
      data = await websocket.receive_text()
      message = json.loads(data)
      response = {"status": "ok", "echo": message}
      await websocket.send_text(json.dumps(response))
  except WebSocketDisconnect:
    # Client disconnected normally - no need to close again
    pass
  except Exception as e:
    # Check if websocket is still open before trying to close
    if websocket.client_state == WebSocketState.CONNECTED:
      await websocket.close(code=1000, reason=str(e))
    print(f"WebSocket error: {e}")

# --- Main application entrypoint ---

if __name__ == "__main__":
  logger.info("Psyche Engine started")
  uvicorn.run(app, port=5010, log_config=None)
  logger.info("Psyche Engine stopped")
