from enum import Enum
from functools import partial
from sqlalchemy import select
from fastapi import APIRouter, Query
from psyche.models.calendar_models import Activity
from psyche.schemas.calendar_schemas import (
    ActivityRead, ActivityCreate, ActivityUpdate, CalendarGenerationRequest)
from psyche.schemas.common_schemas import JobRead
from psyche.services.calendar import generate_calendar
from psyche.fastapi_deps import JobManagerDep, SessionDep
from psyche.crud import add_crud_routes

router = APIRouter(prefix="/calendar")

calendar_tags: list[str | Enum] = ["Calendar"]

@router.post(":generate", response_model=JobRead, tags=calendar_tags)
async def generate(
    body: CalendarGenerationRequest,
    job_manager: JobManagerDep,
    date: str = Query(
        ...,
        description=
        "Date in ISO format (YYYY-MM-DD)")):
  coro = partial(generate_calendar, date=date, request=body)
  return job_manager.submit_job(coro)

add_crud_routes(
    router=router,
    model=Activity,
    read_schema=ActivityRead,
    prefix="/activities",
    tags=calendar_tags,
    methods=["read_all"],
    query_param_to_field={"date": "date"})

add_crud_routes(
    router=router,
    model=Activity,
    update_schema=ActivityUpdate,
    prefix="/activities",
    tags=calendar_tags,
    methods=["update"])
