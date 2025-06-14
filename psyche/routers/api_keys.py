from fastapi import APIRouter, FastAPI, WebSocket, Request, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update
from pydantic import BaseModel
from psyche.db import AiProvider, AsyncSessionDep, ApiKey

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
  new_name: str | None = None
  new_active: bool | None = None

# --- Routes ---

router = APIRouter()

@router.post("/api-key", response_model=ApiKeyRead)
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

@router.delete("/api-key/{key_value}")
async def delete_api_key(key_value: str, db: AsyncSessionDep):
  """Delete an existing API key by its key_value from the URL path."""

  stmt = delete(ApiKey).where(ApiKey.key_value == key_value)
  result = await db.execute(stmt)

  if result.rowcount == 0:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

  await db.commit()

  return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/api-key", response_model=ApiKeyRead)
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

@router.get("/api-keys", response_model=list[ApiKeyRead])
async def get_api_keys(db: AsyncSessionDep):
  result = await db.execute(select(ApiKey))
  api_keys = result.scalars().all()
  return api_keys
