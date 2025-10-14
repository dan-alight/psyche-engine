from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from alembic.config import Config
from alembic import command
from psyche.config import SQLITE_DB_FILE_PATH

SQLITE_DB_URL = f"sqlite+aiosqlite:///{SQLITE_DB_FILE_PATH}"
engine = create_async_engine(SQLITE_DB_URL)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
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

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# --- Dependency Injection ---
async def get_session() -> AsyncGenerator[AsyncSession, None]:
  async with SessionLocal() as session:
    yield session
