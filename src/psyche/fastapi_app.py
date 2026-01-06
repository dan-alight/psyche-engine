import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from psyche.endpoints.goals import router as goals_router
from psyche.endpoints.openai_api_providers import router as openai_api_providers_router
from psyche.endpoints.openai_api_keys import router as openai_api_keys_router
from psyche.endpoints.openai_api_models import router as openai_api_models_router
from psyche.endpoints.calendar import router as calendar_router
from psyche.endpoints.jobs import router as jobs_router
from psyche.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
  yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(
    request: Request, exc: ResourceNotFoundError):
  logger.debug(f"Resource not found handler triggered")
  return JSONResponse(status_code=404, content={"detail": "Resource not found"})

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

app.include_router(goals_router)
app.include_router(openai_api_providers_router)
app.include_router(openai_api_keys_router)
app.include_router(openai_api_models_router)
app.include_router(calendar_router)
app.include_router(jobs_router)
