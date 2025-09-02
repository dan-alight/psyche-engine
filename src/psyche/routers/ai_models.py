from enum import Enum
from fastapi import APIRouter
from sqlalchemy import select
from psyche.models.ai_models import AiModel
from psyche.database import SessionDep
from psyche.schemas.ai_schemas import (AiModelRead, AiModelUpdate)
from psyche.exceptions import ResourceNotFoundError

ai_models_tags: list[str | Enum] = ["AiModels"]

ai_models_router = APIRouter(tags=ai_models_tags)

@ai_models_router.get("/ai-models/active")
async def get_active_models(db: SessionDep):
  stmt = select(AiModel).where(AiModel.active == True)
  result = await db.execute(stmt)
  models = result.scalars().all()
  return models

@ai_models_router.patch(
    "/ai-models/{model_id}", response_model=AiModelRead, tags=ai_models_tags)
async def update_model(request: AiModelUpdate, model_id: int, db: SessionDep):
  get_stmt = select(AiModel).where(AiModel.id == model_id)
  result = await db.execute(get_stmt)
  model_to_update = result.scalar_one_or_none()
  if not model_to_update:
    raise ResourceNotFoundError(resource_type="AiModel", resource_id=model_id)
  if request.active is not None:
    model_to_update.active = request.active

  await db.commit()
  await db.refresh(model_to_update)
  return model_to_update
