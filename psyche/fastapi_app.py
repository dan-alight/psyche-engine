import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from psyche.db import create_db_and_tables
from psyche.routers import api_keys, journal

logger = logging.getLogger("psyche")

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  await create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_keys.router)
# Order is important
app.include_router(journal.stats_router)
app.include_router(journal.router)


@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError):
  logger.warning(
      "Validation error:", exc.errors(), '\n', 'Request body:', await
      request.body())
  return await request_validation_exception_handler(request, exc)
