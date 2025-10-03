from psyche.models.base import Base
from sqlalchemy import Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

class Evaluation(Base):
  __tablename__ = "evaluation"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)

  # an evaluation always corresponds to some specific row in another table, whether a contentful row or a generic grouping entity
  target_table: Mapped[str] = mapped_column(String)
  target_id: Mapped[int] = mapped_column(Integer)  
  # target_context provides information about the state of the target that was evaluated
  target_context: Mapped[dict] = mapped_column(JSON)

  # e.g "sentiment", "summary"
  evaluation_type: Mapped[str] = mapped_column(String)
  evaluation_context: Mapped[dict] = mapped_column(JSON)
  data: Mapped[dict] = mapped_column(JSON)