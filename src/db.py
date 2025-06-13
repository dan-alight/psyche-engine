from typing import Annotated, AsyncGenerator
from enum import Enum as PyEnum
from datetime import datetime

from fastapi import Depends
from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer, String, text, Index, Boolean)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

_SQLITE_FILE = "db.sqlite"
_SQLITE_DB_URL = f"sqlite+aiosqlite:///{_SQLITE_FILE}"

engine = create_async_engine(_SQLITE_DB_URL)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

# --- SQLAlchemy Models ---

class Base(DeclarativeBase):
  pass

class AiProvider(str, PyEnum):
  OPENAI = "openai"
  ANTHROPIC = "anthropic"
  GOOGLE = "google"

class ApiKey(Base):
  __tablename__ = "apikey"

  id: Mapped[int] = mapped_column(primary_key=True)
  key_value: Mapped[str] = mapped_column(String, unique=True)
  provider: Mapped[AiProvider] = mapped_column(Enum(AiProvider))
  name: Mapped[str] = mapped_column(String, unique=True)
  active: Mapped[bool] = mapped_column(Boolean, default=False)

  __table_args__ = (
      Index(
          'ix_apikey_active_provider_unique',
          'provider',
          unique=True,
          postgresql_where=text('active = true'),
          sqlite_where=text('active = 1')), )

class Conversation(Base):
  __tablename__ = "conversation"

  id: Mapped[int] = mapped_column(primary_key=True)
  title: Mapped[str | None] = mapped_column(String)
  last_updated: Mapped[datetime | None] = mapped_column(DateTime)

class Message(Base):
  __tablename__ = "message"

  id: Mapped[int] = mapped_column(primary_key=True)
  conversation_id: Mapped[int] = mapped_column(
      ForeignKey("conversation.id", ondelete="CASCADE"))
  role: Mapped[str] = mapped_column(String)
  content: Mapped[str] = mapped_column(String)
  created_at: Mapped[datetime] = mapped_column(
      DateTime, server_default=text("CURRENT_TIMESTAMP"))
  generated_by: Mapped[str] = mapped_column(String)

# --- Database Initialization ---
async def create_db_and_tables():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

# --- Dependency Injection ---
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionFactory() as session:
    yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
