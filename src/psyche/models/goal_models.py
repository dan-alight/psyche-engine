from sqlalchemy.orm import Mapped, mapped_column
from psyche.models.base import Base
from psyche.models.mixins import IDMixin

class Goal(Base, IDMixin):
  __tablename__ = "goal"

  title: Mapped[str] = mapped_column()
  description: Mapped[str] = mapped_column()
