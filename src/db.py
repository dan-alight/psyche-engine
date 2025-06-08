from typing import Annotated, AsyncGenerator

from sqlmodel import Field, SQLModel, create_engine, Session, Column, DateTime, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime
from fastapi import Depends

_SQLITE_FILE = "db.sqlite"
_SQLITE_DB_URL = f"sqlite+aiosqlite:///{_SQLITE_FILE}"
engine = create_async_engine(_SQLITE_DB_URL)

class ApiKey(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  key_value: str = Field(index=True, unique=True)
  created_at: datetime | None = Field(
      default=None,
      sa_column=Column(DateTime, server_default=text("CURRENT_TIMESTAMP")))

class Conversation(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  title: str | None = Field(default=None)
  last_updated: datetime | None = Field(default=None, nullable=True)

class Message(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  conversation_id: int = Field(
      foreign_key="conversation.id", ondelete="CASCADE")
  role: str
  content: str
  created_at: datetime | None = Field(default=None, nullable=True)
  generated_by: str | None = Field(default=None)

async def create_db_and_tables():
  async with engine.begin() as conn:
    await conn.run_sync(SQLModel.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSession(engine) as session:
    yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
