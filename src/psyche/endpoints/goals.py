from enum import Enum
from fastapi import APIRouter
from psyche.models.goal_models import Goal
from psyche.schemas.goal_schemas import GoalCreate, GoalRead, GoalUpdate
from psyche.schemas.common_schemas import JobRead
from psyche.crud import add_crud_routes
from psyche.fastapi_deps import JobManagerDep
from psyche.services.strategy import generate_strategy

router = APIRouter(prefix="/goals")

goals_tags: list[str | Enum] = ["Goals"]

@router.post("/{id}/strategy:generate", response_model=JobRead, tags=goals_tags)
async def generate(job_manager: JobManagerDep):
  coro = generate_strategy
  return job_manager.submit_job(coro)

add_crud_routes(
    router=router,
    model=Goal,
    read_schema=GoalRead,
    create_schema=GoalCreate,
    update_schema=GoalUpdate,
    tags=goals_tags)
