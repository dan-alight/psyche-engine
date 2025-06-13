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
from sqlmodel import select, delete, update
from sqlalchemy.exc import IntegrityError
from starlette.websockets import WebSocketDisconnect, WebSocketState
from db import create_db_and_tables, AsyncSessionDep, AiProvider, ApiKey
from logconfig import setup_logging

setup_logging()
logger = logging.getLogger("psyche")

# --- Pydantic Models ---

class ApiKeyCreate(BaseModel):
  key_value: str
  provider: AiProvider
  name: str

class ApiKeyRead(BaseModel):
  id: int
  key_value: str
  provider: AiProvider
  name: str
  active: bool

  class Config:
    from_attributes = True

class ApiKeyUpdate(BaseModel):
  key_value: str
  new_name: str | None
  new_active: bool | None

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  await create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173"]

app.add_middleware(CORSMiddleware, allow_origins=origins)

@app.post("/api-key", response_model=ApiKeyRead)
async def create_api_key(request: ApiKeyCreate, db: AsyncSessionDep):
  """Create a new API key."""
  api_key = ApiKey(**request.model_dump())

  try:
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
  except IntegrityError:
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="API key with this value or name already exists")

  return api_key

@app.delete("/api-key/{key_name}")
async def delete_api_key(key_name: str, db: AsyncSessionDep):
  """Delete an existing API key by its name from the URL path."""

  stmt = delete(ApiKey).where(ApiKey.name == key_name)
  result = await db.execute(stmt)

  if result.rowcount == 0:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

  await db.commit()

  return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/api-key", response_model=ApiKeyRead)
async def update_api_key(request: ApiKeyUpdate, db: AsyncSessionDep):
  """
  Update an API key's name or active status.

  - The key to update is identified by its `key_value`.
  - If `new_active` is set to `True`, any other key for the same provider
    that is currently active will be deactivated to satisfy the unique
    constraint. This is done atomically within the same transaction.
  - Updating the name is subject to a unique constraint check.
  """

  get_stmt = select(ApiKey).where(
      ApiKey.key_value == request.key_value).with_for_update()
  result = await db.execute(get_stmt)
  api_key_to_update = result.scalar_one_or_none()

  if not api_key_to_update:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key with the given value not found.")

  if request.new_active is True:
    deactivate_stmt = (
        update(ApiKey).where(
            ApiKey.provider == api_key_to_update.provider,
            ApiKey.active == True, ApiKey.id
            != api_key_to_update.id).values(active=False))
    await db.execute(deactivate_stmt)

  if request.new_name is not None:
    api_key_to_update.name = request.new_name
  if request.new_active is not None:
    api_key_to_update.active = request.new_active

  try:
    await db.commit()
    await db.refresh(api_key_to_update)
  except IntegrityError:
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An API key with the new name already exists.")

  return api_key_to_update

@app.get("/api-keys", response_model=list[ApiKeyRead])
async def get_api_keys(db: AsyncSessionDep):
  result = await db.execute(select(ApiKey))
  api_keys = result.scalars().all()
  return api_keys

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

# --- Main application entrypoint ---

if __name__ == "__main__":
  logger.info("Psyche Engine started")
  uvicorn.run(app, port=5010, log_config=None)
  logger.info("Psyche Engine stopped")
