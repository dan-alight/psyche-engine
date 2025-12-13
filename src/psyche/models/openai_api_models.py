from psyche.models.base import Base
from psyche.models.mixins import IDMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index, event, update

class OpenAiApiProvider(Base, IDMixin):
  __tablename__ = "openai_api_provider"
  name: Mapped[str] = mapped_column()
  base_url: Mapped[str] = mapped_column()

class OpenAiApiKey(Base, IDMixin):
  __tablename__ = "openai_api_key"
  key: Mapped[str] = mapped_column()
  provider_id: Mapped[int] = mapped_column(
      ForeignKey("openai_api_provider.id", ondelete="CASCADE"))
  active: Mapped[bool] = mapped_column(default=True)

  provider: Mapped["OpenAiApiProvider"] = relationship()

  __table_args__ = (
      Index(
          "ix_unique_active_key_per_provider",
          "provider_id",
          unique=True,
          sqlite_where=(active == True)), )

class OpenAiApiModel(Base, IDMixin):
  __tablename__ = "openai_api_model"
  name: Mapped[str] = mapped_column()
  provider_id: Mapped[int] = mapped_column(
      ForeignKey("openai_api_provider.id", ondelete="CASCADE"))
  bookmarked: Mapped[bool] = mapped_column(default=False)

  provider: Mapped["OpenAiApiProvider"] = relationship()

def deactivate_other_keys(mapper, connection, target):
  if target.active:
    stmt = update(OpenAiApiKey).where(
        OpenAiApiKey.provider_id == target.provider_id, OpenAiApiKey.id
        != target.id, OpenAiApiKey.active == True).values(active=False)
    connection.execute(stmt)

event.listen(OpenAiApiKey, "before_insert", deactivate_other_keys)
event.listen(OpenAiApiKey, "before_update", deactivate_other_keys)
