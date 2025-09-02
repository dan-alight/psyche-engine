import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from psyche.routers import api_keys, ai_providers, chat, conversations, journal_entries, ai_models
from psyche.exceptions import DuplicateResourceError, ExternalAPIError, ResourceNotFoundError, InvalidStateError
from sqlalchemy.exc import IntegrityError
from fastapi.responses import PlainTextResponse
from openai import APIError

logger = logging.getLogger("uvicorn.access")

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
  return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
  method = request.method
  path = str(request.url.path)
  logger.error(f"Validation error for {method} to '{path}': {exc}")
  return PlainTextResponse(
      str(exc), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
  return JSONResponse(
      status_code=status.HTTP_409_CONFLICT,  # conflict
      content={"detail": str(exc.orig)},
  )

@app.exception_handler(APIError)
async def api_error_exception_handler(request: Request, exc: APIError):
  return JSONResponse(
      status_code=status.HTTP_502_BAD_GATEWAY,
      content={"detail": str(exc)},
  )

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_exception_handler(
    request: Request, exc: ResourceNotFoundError):
  return JSONResponse(
      status_code=status.HTTP_404_NOT_FOUND,
      content={"detail": exc.message},
  )

origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Order is important
app.include_router(ai_providers.ai_providers_router)
app.include_router(ai_providers.ai_providers_crud_router)
app.include_router(ai_models.ai_models_router)
app.include_router(api_keys.api_keys_crud_router)
app.include_router(journal_entries.journal_entries_router)
app.include_router(journal_entries.journal_entries_crud_router)
app.include_router(chat.chat_router)
app.include_router(conversations.conversations_crud_router)
