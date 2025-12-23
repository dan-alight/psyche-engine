from fastapi import APIRouter
from sqlalchemy import select
from psyche.models.openai_api_models import OpenAiApiModel
from psyche.schemas.openai_api_schemas import (
    OpenAiApiModelCreate,
    OpenAiApiModelRead,
    OpenAiApiModelUpdate,
)
from psyche.crud import add_crud_routes
from psyche.fastapi_deps import SessionDep

router = APIRouter(prefix="/openai-api-models")

@router.get(
    "/bookmarked",
    response_model=list[OpenAiApiModelRead],
    tags=["OpenAI API Models"])
async def get_bookmarked_models(db: SessionDep):
  result = await db.scalars(
      select(OpenAiApiModel).where(OpenAiApiModel.bookmarked == True))
  return result.all()

add_crud_routes(
    router=router,
    model=OpenAiApiModel,
    read_schema=OpenAiApiModelRead,
    update_schema=OpenAiApiModelUpdate,
    tags=["OpenAI API Models"],
    methods=["read_all", "update"],
)
