from typing import Annotated, AsyncGenerator
from enum import Enum as PyEnum
from datetime import datetime
from fastapi import Depends
from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, text, Index, Boolean,
    UniqueConstraint)
from sqlalchemy.engine import Connection
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from alembic.config import Config
from alembic import command

_SQLITE_FILE = "db.sqlite"
_SQLITE_DB_URL = f"sqlite+aiosqlite:///{_SQLITE_FILE}"

engine = create_async_engine(_SQLITE_DB_URL)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

# --- SQLAlchemy Models ---

class Base(DeclarativeBase):
  pass

class AiProvider(Base):
  __tablename__ = "aiprovider"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String, unique=True)
  base_url: Mapped[str] = mapped_column(String)

class ApiKey(Base):
  __tablename__ = "apikey"

  id: Mapped[int] = mapped_column(primary_key=True)
  key_value: Mapped[str] = mapped_column(String)
  name: Mapped[str] = mapped_column(String)
  provider_id: Mapped[int] = mapped_column(
      ForeignKey("aiprovider.id", ondelete="CASCADE"))
  active: Mapped[bool] = mapped_column(Boolean, default=False)

  provider: Mapped["AiProvider"] = relationship("AiProvider")

  __table_args__ = (
      Index(
          'ix_apikey_active_provider_unique',
          'provider_id',
          unique=True,
          postgresql_where=text('active = true'),
          sqlite_where=text('active = 1')),
      UniqueConstraint('provider_id', 'name', name='uq_apikey_provider_name'),
      UniqueConstraint(
          'provider_id', 'key_value', name='uq_apikey_provider_key_value'),
  )

class JournalEntry(Base):
  __tablename__ = "journalentry"

  id: Mapped[int] = mapped_column(primary_key=True)
  content: Mapped[str] = mapped_column(String)
  created_at: Mapped[datetime] = mapped_column(
      DateTime, server_default=text("CURRENT_TIMESTAMP"))

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

def run_alembic_upgrade():
  """
  Runs the Alembic upgrade command to bring the database to the latest version.
  """
  alembic_cfg = Config("alembic.ini")
  command.upgrade(alembic_cfg, "head")

# --- Dependency Injection ---
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
  async with AsyncSessionFactory() as session:
    yield session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
