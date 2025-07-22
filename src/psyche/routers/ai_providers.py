from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from fastcrud import FastCRUD, crud_router
from typing import Annotated
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, update
from psyche.models.ai_models import AiProvider, ApiKey, AiModel
from psyche.database import SessionDep, get_async_session
from psyche.schemas.ai_schemas import (
    AiProviderCreate, AiProviderUpdate, AiProviderRead, ApiKeyCreate,
    ApiKeyUpdate, ApiKeyRead, AiModelRead, AiModelUpdate)
from openai import AsyncOpenAI, APIError

# --- Dependency Injection ---

_openai_client_cache = {}

async def get_async_openai_client(
    provider_id: int, db: SessionDep) -> AsyncOpenAI:
  """
    Dependency to create and cache an AsyncOpenAI client for a specific provider.
    """
  provider = await db.get(AiProvider, provider_id)
  if not provider:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

  active_api_key = await db.scalar(
      select(ApiKey).where(
          ApiKey.provider_id == provider_id, ApiKey.active == True))
  if not active_api_key:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No active API key found for this provider",
    )

  cached_client, cached_base_url, cached_api_key = _openai_client_cache.get(
      provider_id, (None, None, None))

  if (cached_client and cached_base_url == provider.base_url
      and cached_api_key == active_api_key.key_value):
    return cached_client

  new_client = AsyncOpenAI(
      base_url=provider.base_url,
      api_key=active_api_key.key_value,
  )
  _openai_client_cache[provider_id] = (
      new_client, provider.base_url, active_api_key.key_value)

  return new_client

OpenAIDep = Annotated[AsyncOpenAI, Depends(get_async_openai_client)]

# --- Routes ---

aiproviders_tags: list[str | Enum] = ["AiProviders"]

aiproviders_crud_router = crud_router(
    session=get_async_session,
    model=AiProvider,
    create_schema=AiProviderCreate,
    update_schema=AiProviderUpdate,
    select_schema=AiProviderRead,
    path="/ai-providers",
    tags=aiproviders_tags,
    included_methods=["create", "read_multi", "delete", "update"])

aiproviders_router = APIRouter(tags=aiproviders_tags)

@aiproviders_router.get(
    "/ai-providers/{provider_id}/models", tags=aiproviders_tags)
async def get_provider_models(
    provider_id: int,
    client: OpenAIDep,
    db: SessionDep,
    refresh: bool = Query(
        False,
        description=
        "Force a refresh of the model list directly from the provider, bypassing the cache."
    )):
  """
    Get available models from a provider.

    Args:
      refresh: If true, will fetch the model list from the provider's API and
        update the database. Otherwise, will return the currently stored models.
    """
  if refresh:
    try:
      # Fetch the current list of models from the provider's API
      models_from_api = await client.models.list()
      api_model_names = {model.id for model in models_from_api.data}

      # Fetch the names of existing models from the database
      existing_models_stmt = select(
          AiModel.name).where(AiModel.provider_id == provider_id)
      result = await db.execute(existing_models_stmt)
      db_model_names = {name for (name, ) in result}

      # Determine which models to add and which to delete
      models_to_add = api_model_names - db_model_names
      models_to_delete = db_model_names - api_model_names

      # Perform additions and deletions in a single transaction
      if models_to_add:
        db.add_all(
            [
                AiModel(provider_id=provider_id, name=name)
                for name in models_to_add
            ])

      if models_to_delete:
        await db.execute(
            delete(AiModel).where(
                AiModel.provider_id == provider_id,
                AiModel.name.in_(models_to_delete)))

      # Commit the transaction if any changes were made
      if models_to_add or models_to_delete:
        await db.commit()

      # Return the updated list of all models from the database
      all_models_stmt = select(AiModel).where(
          AiModel.provider_id == provider_id)
      result = await db.execute(all_models_stmt)
      return result.scalars().all()

    except APIError as e:
      # It's good practice to roll back the transaction on API error
      await db.rollback()
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail=f"Error fetching models from provider: {e.message}",
      )
  else:
    # Return models directly from the database
    stmt = select(AiModel).where(AiModel.provider_id == provider_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@aiproviders_router.patch(
    "/ai-providers/{provider_id}/models/{model_id}",
    response_model=AiModelRead,
    tags=aiproviders_tags)
async def update_model(request: AiModelUpdate, model_id: int, db: SessionDep):
  get_stmt = select(AiModel).where(AiModel.id == model_id).with_for_update()
  result = await db.execute(get_stmt)
  model_to_update = result.scalar_one_or_none()
  if not model_to_update:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
  if request.active is not None:
    model_to_update.active = request.active

  await db.commit()
  await db.refresh(model_to_update)
  return model_to_update

api_keys_tags: list[str | Enum] = ["ApiKeys"]

api_keys_crud_router = crud_router(
    session=get_async_session,
    model=ApiKey,
    create_schema=ApiKeyCreate,
    update_schema=ApiKeyUpdate,
    select_schema=ApiKeyRead,
    path="/api-keys",
    tags=api_keys_tags,
    included_methods=["create", "read_multi", "delete"])

@api_keys_crud_router.patch(
    "/api-keys/{id}", response_model=ApiKeyRead, tags=api_keys_tags)
async def update_api_key(request: ApiKeyUpdate, id: int, db: SessionDep):
  """
  Update an API key's name or active status.

  - The key to update is identified by its `key_value`.
  - If `new_active` is set to `True`, any other key for the same provider
    that is currently active will be deactivated to satisfy the unique
    constraint. This is done atomically within the same transaction.
  - Updating the name is subject to a unique constraint check.
  """

  get_stmt = select(ApiKey).where(ApiKey.id == id).with_for_update()
  result = await db.execute(get_stmt)
  api_key_to_update = result.scalar_one_or_none()

  if not api_key_to_update:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="API key with the given value not found.")

  if request.active is True:
    deactivate_stmt = (
        update(ApiKey).where(
            ApiKey.provider_id == api_key_to_update.provider_id,
            ApiKey.active == True, ApiKey.id
            != api_key_to_update.id).values(active=False))
    await db.execute(deactivate_stmt)

  if request.name is not None:
    api_key_to_update.name = request.name
  if request.active is not None:
    api_key_to_update.active = request.active

  try:
    await db.commit()
    await db.refresh(api_key_to_update)
  except IntegrityError:
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An API key with the new name already exists.")

  return api_key_to_update
