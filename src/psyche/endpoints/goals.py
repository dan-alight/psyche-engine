from enum import Enum
from functools import partial
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from psyche.models.goal_models import Goal, GoalStrategy
from psyche.schemas.goal_schemas import (
    GoalCreate, GoalRead, GoalUpdate, StrategyGenerationRequest,
    GoalStrategyRead)
from psyche.schemas.job_schemas import JobRead
from psyche.crud import add_crud_routes
from psyche.fastapi_deps import JobManagerDep, SessionDep
from psyche.services.strategy import generate_strategy

router = APIRouter(prefix="/goals")

goals_tags: list[str | Enum] = ["Goals"]

@router.post("/{id}/strategy:generate", response_model=JobRead, tags=goals_tags)
async def generate(
    id: int, body: StrategyGenerationRequest, job_manager: JobManagerDep):
  coro = partial(generate_strategy, id=id, request=body)
  return job_manager.submit_job(coro)

@router.get("/{id}/strategy", response_model=GoalStrategyRead, tags=goals_tags)
async def read_strategy(id: int, db: SessionDep):
  item = await db.scalar(select(GoalStrategy).where(GoalStrategy.goal_id == id))
  if not item:
    raise HTTPException(status_code=404, detail="Item not found")
  return item

add_crud_routes(
    router=router,
    model=Goal,
    read_schema=GoalRead,
    create_schema=GoalCreate,
    update_schema=GoalUpdate,
    tags=goals_tags)
