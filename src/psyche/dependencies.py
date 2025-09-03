from typing import Annotated
from psyche.database import get_session
from psyche.openai_clients import get_openai_client
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_session)]
OpenAIDep = Annotated[AsyncOpenAI, Depends(get_openai_client)]
