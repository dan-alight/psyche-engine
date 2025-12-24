import asyncio
from datetime import date as datetime_date
from psyche.schemas.calendar_schemas import CalendarGenerationRequest

async def generate_calendar(date: str, request: CalendarGenerationRequest) -> None:
  await asyncio.sleep(1)