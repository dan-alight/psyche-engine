import json
from contextlib import asynccontextmanager
import logging
from logging.handlers import RotatingFileHandler
import time
import datetime
import uvicorn
from pydantic import BaseModel
from uvicorn.logging import DefaultFormatter
from fastapi import FastAPI, WebSocket, Request, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.websockets import WebSocketDisconnect, WebSocketState
from psyche.db import create_db_and_tables, AsyncSessionDep, AiProvider, ApiKey
from psyche.routers import api_keys
from logconfig import setup_logging

setup_logging()
logger = logging.getLogger("psyche")

# --- Pydantic Models ---

class JournalEntryCreate(BaseModel):
  content: str

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  await create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)
app.include_router(api_keys.router)

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.websocket("/chat")
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

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError):
  # Print/log the detailed errors
  print("Validation error:", exc.errors())
  print("Request body:", await request.body())

  # Optionally customize the response
  return await request_validation_exception_handler(request, exc)

# --- Main application entrypoint ---

if __name__ == "__main__":
  logger.info("Psyche Engine started")
  uvicorn.run(app, port=5010, log_config=None)
  logger.info("Psyche Engine stopped")
