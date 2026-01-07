from enum import Enum
from functools import partial
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from psyche.models.goal_models import Goal, GoalStrategy
from psyche.schemas.goal_schemas import (
    GoalCreate, GoalRead, GoalUpdate, StrategyGenerationRequest,
    GoalStrategyRead, GoalMetadata)
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
async def get_strategy(id: int, db: SessionDep):
  item = await db.scalar(select(GoalStrategy).where(GoalStrategy.goal_id == id))
  if not item:
    raise HTTPException(status_code=404, detail="Item not found")
  return item

@router.get("/metadata", response_model=list[GoalMetadata], tags=goals_tags)
async def get_metadata(db: SessionDep):
  stmt = select(
      Goal.id.label("goal_id"),
      GoalStrategy.id.is_not(None).label("has_strategy")).outerjoin(
          GoalStrategy, Goal.id == GoalStrategy.goal_id)
  res = await db.execute(stmt)
  return res.mappings().all()

add_crud_routes(
    router=router,
    model=Goal,
    read_schema=GoalRead,
    create_schema=GoalCreate,
    update_schema=GoalUpdate,
    tags=goals_tags)
