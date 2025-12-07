from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from psyche.database import get_db

SessionDep = Annotated[AsyncSession, Depends(get_db)]
