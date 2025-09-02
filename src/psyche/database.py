import logging
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from alembic.config import Config
from alembic import command
from psyche.config import SQLITE_DB_FILE_PATH

_SQLITE_DB_URL = f"sqlite+aiosqlite:///{SQLITE_DB_FILE_PATH}"
_engine = create_async_engine(_SQLITE_DB_URL)

@event.listens_for(_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
  """Enable foreign key constraints for SQLite connections."""
  cursor = dbapi_connection.cursor()
  cursor.execute("PRAGMA foreign_keys=ON")
  cursor.close()

def upgrade_database():
  """
  Runs the Alembic upgrade command to bring the database to the latest version.
  """
  alembic_cfg = Config("alembic.ini")
  command.upgrade(alembic_cfg, "head")

SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)

# --- Dependency Injection ---
async def get_session() -> AsyncGenerator[AsyncSession, None]:
  async with SessionLocal() as session:
    yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
