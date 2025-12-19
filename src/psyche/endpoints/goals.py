from fastapi import APIRouter
from psyche.models.goal_models import Goal
from psyche.schemas.goal_schemas import GoalCreate, GoalRead, GoalUpdate
from psyche.crud import add_crud_routes

router = APIRouter(prefix="/goals")

add_crud_routes(
    router=router,
    model=Goal,
    read_schema=GoalRead,
    create_schema=GoalCreate,
    update_schema=GoalUpdate,
    tags=["Goals"])
