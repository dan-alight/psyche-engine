from enum import Enum
from fastcrud import crud_router
from sqlalchemy import select, update
from psyche.models.openai_api_models import ApiKey
from psyche.database import get_session
from psyche.dependencies import SessionDep
from psyche.schemas.ai_schemas import (ApiKeyCreate, ApiKeyUpdate, ApiKeyRead)
from psyche.exceptions import ResourceNotFoundError

api_keys_tags: list[str | Enum] = ["ApiKeys"]

api_keys_crud_router = crud_router(
    session=get_session,
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

  get_stmt = select(ApiKey).where(ApiKey.id == id)
  result = await db.execute(get_stmt)
  api_key_to_update = result.scalar_one_or_none()

  if not api_key_to_update:
    raise ResourceNotFoundError(resource_type="ApiKey", resource_id=id)

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

  await db.commit()
  await db.refresh(api_key_to_update)

  return api_key_to_update
