import logging
from sqlalchemy import select
from psyche.database import SessionLocal
from psyche.models.goal_models import Goal
from psyche.schemas.goal_schemas import StrategyGenerationRequest

logger = logging.getLogger(__name__)

async def generate_strategy(id: int, request: StrategyGenerationRequest):
  async with SessionLocal() as db:
    goal = await db.scalar(select(Goal).where(Goal.id == id))
    if goal:
      logger.debug(
          f"Generating strategy for goal {goal.title} with model {request.model_id}"
      )
