from datetime import datetime
from psyche.models.base import Base
from sqlalchemy import Integer, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

class JournalEntry(Base):
  __tablename__ = "journal_entry"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  content: Mapped[str] = mapped_column(String)
  created_at: Mapped[datetime] = mapped_column(
      DateTime, server_default=text("CURRENT_TIMESTAMP"))
