from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

SQLITE_DB_FILE_NAME = "db.sqlite"
SQLITE_DB_URL = f"sqlite+aiosqlite:///{SQLITE_DB_FILE_NAME}"

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
