from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint
from psyche.models.base import Base
from psyche.models.mixins import IDMixin, TimestampMixin

class Goal(Base, IDMixin, TimestampMixin):
  __tablename__ = "goal"

  title: Mapped[str] = mapped_column()
  description: Mapped[str] = mapped_column()
  initial_progress: Mapped[str] = mapped_column()
  strategy_guidelines: Mapped[str] = mapped_column()
  active: Mapped[bool] = mapped_column(default=False)

class GoalProgressUpdate(Base, IDMixin, TimestampMixin):
  __tablename__ = "goal_progress_update"

  goal_id: Mapped[int] = mapped_column(
      ForeignKey("goal.id", ondelete="CASCADE"))
  progress: Mapped[str] = mapped_column()

class GoalStrategy(Base, IDMixin):
  __tablename__ = "goal_strategy"
  goal_id: Mapped[int] = mapped_column(
      ForeignKey("goal.id", ondelete="CASCADE"), unique=True)
  strategy: Mapped[str] = mapped_column()
