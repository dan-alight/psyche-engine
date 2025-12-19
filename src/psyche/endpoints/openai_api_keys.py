from fastapi import APIRouter
from psyche.models.openai_api_models import OpenAiApiKey
from psyche.schemas.openai_api_schemas import (
    OpenAiApiKeyCreate,
    OpenAiApiKeyRead,
    OpenAiApiKeyUpdate,
)
from psyche.crud import add_crud_routes

router = APIRouter(prefix="/openai-api-keys")

add_crud_routes(
    router=router,
    model=OpenAiApiKey,
    read_schema=OpenAiApiKeyRead,
    create_schema=OpenAiApiKeyCreate,
    update_schema=OpenAiApiKeyUpdate,
    tags=["OpenAI API Keys"],
    methods=["read_one", "read_all", "update", "delete"],
)
