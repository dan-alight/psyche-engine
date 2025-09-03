from enum import Enum
from fastapi import APIRouter
from psyche.dependencies import SessionDep

ai_agents_router = APIRouter()

@ai_agents_router.patch("/ai-agents")
async def configure_agent(db: SessionDep):

  pass
