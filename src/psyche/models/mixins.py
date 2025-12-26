from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text

class IDMixin:
  id: Mapped[int] = mapped_column(primary_key=True)

class TimestampMixin:
  created_at: Mapped[datetime] = mapped_column(
      server_default=text("CURRENT_TIMESTAMP"))
