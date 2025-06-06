from sqlmodel import Field, SQLModel, create_engine
from datetime import datetime

_SQLITE_FILE = "db.sqlite"
_SQLITE_DB_URL = f"sqlite:///{_SQLITE_FILE}"
_SCHEMA_VERSION = 1

class SchemaVersion(SQLModel, table=True):
  version: int = Field(primary_key=True)
  applied_at: datetime | None = Field(default=None, nullable=True)

class ApiKey(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  key_value: str = Field(index=True, unique=True)
  created_at: datetime | None = Field(default=None, nullable=True)

class Conversation(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  title: str | None = Field(default=None)
  last_updated: datetime | None = Field(default=None, nullable=True)

class Message(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  conversation_id: int = Field(foreign_key="conversation.id", ondelete="CASCADE")
  role: str
  content: str
  created_at: datetime | None = Field(default=None, nullable=True)
  generated_by: str | None = Field(default=None)

connect_args = {"check_same_thread": False}
sql_engine = create_engine(_SQLITE_DB_URL, connect_args=connect_args)

def create_db_and_tables():
  SQLModel.metadata.create_all(sql_engine)
