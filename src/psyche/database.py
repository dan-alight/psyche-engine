import os
from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB_FILENAME = os.getenv("SQLITE_DB_FILENAME", "db.sqlite")
SQLITE_DB_URL = f"sqlite+aiosqlite:///{SQLITE_DB_FILENAME}"

engine = create_async_engine(SQLITE_DB_URL)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
  cursor = dbapi_connection.cursor()
  cursor.execute("PRAGMA foreign_keys=ON")
  cursor.close()

def run_migrations():
  alembic_cfg = Config("alembic.ini")
  alembic_cfg.attributes["configure_logger"] = False
  command.upgrade(alembic_cfg, "head")

SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
  async with SessionLocal() as session:
    yield session
