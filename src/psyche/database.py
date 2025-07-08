from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from alembic.config import Config
from alembic import command
from psyche.config import SQLITE_DB_FILE_PATH

_SQLITE_DB_URL = f"sqlite+aiosqlite:///{SQLITE_DB_FILE_PATH}"

_engine = create_async_engine(_SQLITE_DB_URL)
_async_session = async_sessionmaker(_engine, expire_on_commit=False)

def run_alembic_upgrade():
  """
  Runs the Alembic upgrade command to bring the database to the latest version.
  """
  alembic_cfg = Config("alembic.ini")
  command.upgrade(alembic_cfg, "head")

# --- Dependency Injection ---

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
  async with _async_session() as session:
    yield session

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
