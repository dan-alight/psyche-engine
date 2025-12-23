from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from openai import AsyncOpenAI
from psyche.database import get_db
from psyche.openai_clients import get_openai_client
from psyche.job_manager import get_job_manager, JobManager

SessionDep = Annotated[AsyncSession, Depends(get_db)]
OpenAiDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]
JobManagerDep = Annotated[JobManager, Depends(get_job_manager)]