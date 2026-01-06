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

add_crud_routes(
    router=router,
    model=OpenAiApiModel,
    read_schema=OpenAiApiModelRead,
    update_schema=OpenAiApiModelUpdate,
    tags=["OpenAI API Models"],
    methods=["read_all", "update"],
)
