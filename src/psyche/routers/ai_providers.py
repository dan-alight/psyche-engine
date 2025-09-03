from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from fastcrud import FastCRUD, crud_router
from typing import Annotated
from sqlalchemy import select, delete
from psyche.models.ai_models import AiProvider, ApiKey, AiModel
from psyche.database import get_session
from psyche.dependencies import SessionDep
from psyche.schemas.ai_schemas import (
    AiProviderCreate, AiProviderUpdate, AiProviderRead)
from psyche.custom_endpoint_creator import CustomEndpointCreator
from psyche.dependencies import OpenAIDep

ai_providers_tags: list[str | Enum] = ["AiProviders"]

ai_providers_crud_router = crud_router(
    session=get_session,
    model=AiProvider,
    create_schema=AiProviderCreate,
    update_schema=AiProviderUpdate,
    select_schema=AiProviderRead,
    endpoint_creator=CustomEndpointCreator,
    path="/ai-providers",
    tags=ai_providers_tags,
    included_methods=["create", "read_multi", "delete", "update"])

ai_providers_router = APIRouter(tags=ai_providers_tags)

@ai_providers_router.get(
    "/ai-providers/{provider_id}/ai-models", tags=ai_providers_tags)
async def get_models(
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
    all_models_stmt = select(AiModel).where(AiModel.provider_id == provider_id)
    result = await db.execute(all_models_stmt)
    return result.scalars().all()

  else:
    # Return models directly from the database
    stmt = select(AiModel).where(AiModel.provider_id == provider_id)
    result = await db.execute(stmt)
    return result.scalars().all()
