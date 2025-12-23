from datetime import date as datetime_date
from sqlalchemy.orm import Mapped, mapped_column
from psyche.models.base import Base
from psyche.models.mixins import IDMixin

class Activity(Base, IDMixin):
  __tablename__ = "activity"

  description: Mapped[str] = mapped_column()
  date: Mapped[datetime_date] = mapped_column()
  completed: Mapped[bool] = mapped_column(default=False)
