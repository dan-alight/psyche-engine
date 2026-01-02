import asyncio
from datetime import date as datetime_date
from psyche.schemas.calendar_schemas import CalendarGenerationRequest
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
)
from openai import APIConnectionError
from sqlalchemy import select

async def generate_calendar(
    date: str, request: CalendarGenerationRequest) -> None:
  await asyncio.sleep(10)
