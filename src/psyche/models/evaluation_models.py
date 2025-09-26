from psyche.models.base import Base
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

class Evaluation(Base):
  __tablename__ = "evaluation"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)

  # an evaluation always corresponds to some row in another table
  target_table: Mapped[str] = mapped_column(String)
  target_id: Mapped[int] = mapped_column(Integer)
  # target_context provides e.g version (in the case of journal_entry)
  target_context: Mapped[dict] = mapped_column(JSON)

  evaluation_type: Mapped[str] = mapped_column(String)
  evaluation_context: Mapped[dict] = mapped_column(JSON)
  data: Mapped[dict] = mapped_column(JSON)
  