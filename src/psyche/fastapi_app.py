import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from psyche.routers import ai_providers, journal, chat
from fastapi.routing import APIRoute
from psyche.schemas.chat_schemas import (
    ConversationMessageCreate, ConversationMessageRead, ConversationRead,
    ConversationCreate, ConversationUpdate)
from psyche.models.chat_models import Conversation

logger = logging.getLogger("psyche")

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  yield

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Order is important
app.include_router(ai_providers.aiproviders_router)
app.include_router(ai_providers.aiproviders_crud_router)
app.include_router(ai_providers.api_keys_crud_router)
app.include_router(journal.journal_router)
app.include_router(journal.journal_crud_router)
app.include_router(chat.chat_router)
app.include_router(chat.conversation_crud_router)

@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError):
  logger.warning(
      "Validation error:", exc.errors(), '', 'Request body:', await
      request.body())
  return await request_validation_exception_handler(request, exc)
