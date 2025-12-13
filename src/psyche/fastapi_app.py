from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psyche.endpoints.goals import router as goals_router
from psyche.endpoints.openai_api_providers import router as openai_api_providers_router
from psyche.endpoints.openai_api_keys import router as openai_api_keys_router

@asynccontextmanager
async def lifespan(app: FastAPI):
  # Setup code here (e.g., connect to database)
  yield
  # Teardown code here (e.g., disconnect from database)

app = FastAPI(lifespan=lifespan)

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
