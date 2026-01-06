import logging
import re
from sqlalchemy import select
from openai import APIConnectionError
from psyche.database import SessionLocal
from psyche.models.goal_models import Goal, GoalStrategy
from psyche.models.openai_api_models import OpenAiApiModel
from psyche.schemas.goal_schemas import StrategyGenerationRequest
from psyche.prompting import jinja_env
from psyche.openai_clients import get_openai_client
from psyche.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)

async def generate_strategy(id: int, request: StrategyGenerationRequest):
  async with SessionLocal() as db:
    goal = await db.scalar(select(Goal).where(Goal.id == id))
    if goal is None:
      raise ResourceNotFoundError()
    model = await db.scalar(
        select(OpenAiApiModel).where(OpenAiApiModel.id == request.model_id))
    if model is None:
      raise ResourceNotFoundError()
  template = jinja_env.get_template("strategy.j2")
  prompt = template.render(goal=goal)

  client = await get_openai_client(model.provider_id)
  res = await client.chat.completions.create(
      model=model.name,
      messages=[{
          "role": "user",
          "content": prompt
      }],
  )
  content = res.choices[0].message.content
  if content:
    strategy = re.sub(
        r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    async with SessionLocal() as db:
      db.add(GoalStrategy(goal_id=goal.id, strategy=strategy))
      await db.commit()
