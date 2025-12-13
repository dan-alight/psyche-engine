from fastapi import APIRouter, Query
from sqlalchemy import select, delete
from psyche.fastapi_deps import SessionDep, OpenAiDep
from psyche.models.openai_api_models import OpenAiApiProvider, OpenAiApiKey, OpenAiApiModel
from psyche.schemas.openai_api_schemas import (
    OpenAiApiProviderCreate,
    OpenAiApiProviderRead,
    OpenAiApiProviderUpdate,
    OpenAiApiKeyCreate,
    OpenAiApiKeyRead,
    OpenAiApiKeyUpdate,
    OpenAiApiModelRead,
)
from psyche.crud import add_crud_routes

router = APIRouter(prefix="/openai_api_providers")

@router.get("/{pid}/models", response_model=list[OpenAiApiModelRead])
async def get_models(
    pid: int, db: SessionDep, client: OpenAiDep, refresh: bool = Query(False)):
  if refresh:
    remote_model_list = await client.models.list()
    remote_model_names = {model.id for model in remote_model_list.data}
    result = await db.scalars(
        select(OpenAiApiModel.name).where(OpenAiApiModel.provider_id == pid))
    db_model_names = set(result)

    new_names = remote_model_names - db_model_names
    dropped_names = db_model_names - remote_model_names

    if new_names:
      db.add_all(
          [OpenAiApiModel(provider_id=pid, name=name) for name in new_names])
    if dropped_names:
      await db.execute(
          delete(OpenAiApiModel).where(
              OpenAiApiModel.provider_id == pid,
              OpenAiApiModel.name.in_(dropped_names)))
    await db.commit()

    result = await db.scalars(
        select(OpenAiApiModel).where(OpenAiApiModel.provider_id == pid))
    return result.all()

  else:
    result = await db.scalars(
        select(OpenAiApiModel).where(OpenAiApiModel.provider_id == pid))
    return result.all()

add_crud_routes(
    router, OpenAiApiProvider, OpenAiApiProviderRead, OpenAiApiProviderCreate,
    OpenAiApiProviderUpdate)

add_crud_routes(
    router,
    OpenAiApiKey,
    OpenAiApiKeyRead,
    OpenAiApiKeyCreate,
    OpenAiApiKeyUpdate,
    prefix="/{pid}/keys",
    tags=["OpenAI API Keys"],
    methods=["read_all", "create"],
    url_param_to_field={"pid": "provider_id"},
)
