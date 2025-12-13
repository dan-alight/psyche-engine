from fastapi import APIRouter
from psyche.models.openai_api_models import OpenAiApiKey
from psyche.schemas.openai_api_schemas import (
    OpenAiApiKeyCreate,
    OpenAiApiKeyRead,
    OpenAiApiKeyUpdate,
)
from psyche.crud import add_crud_routes

router = APIRouter(prefix="/openai_api_keys")

add_crud_routes(
    router,
    OpenAiApiKey,
    OpenAiApiKeyRead,
    OpenAiApiKeyCreate,
    OpenAiApiKeyUpdate,
    tags=["OpenAI API Keys"],
    methods=["read_one", "update", "delete"],
)
