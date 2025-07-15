from psyche.models.base import Base
from sqlalchemy import (
    ForeignKey, Integer, String, Boolean, text, Index, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

class AiProvider(Base):
  __tablename__ = "ai_provider"
  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String, unique=True)
  base_url: Mapped[str] = mapped_column(String)

class ApiKey(Base):
  __tablename__ = "api_key"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  key_value: Mapped[str] = mapped_column(String)
  name: Mapped[str] = mapped_column(String)
  provider_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("ai_provider.id", ondelete="CASCADE"))
  active: Mapped[bool] = mapped_column(Boolean, default=False)

  provider: Mapped["AiProvider"] = relationship("AiProvider")

  __table_args__ = (
      Index(
          'ix_api_key_active_provider_unique',
          'provider_id',
          unique=True,
          postgresql_where=text('active = true'),
          sqlite_where=text('active = 1')),
      UniqueConstraint('provider_id', 'name', name='uq_api_key_provider_name'),
      UniqueConstraint(
          'provider_id', 'key_value', name='uq_api_key_provider_key_value'),
  )

class AiModel(Base):
  __tablename__ = "ai_model"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String)
  provider_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("ai_provider.id", ondelete="CASCADE"))
  active: Mapped[bool] = mapped_column(Boolean, default=False)

  provider: Mapped["AiProvider"] = relationship("AiProvider")

  __table_args__ = (
      UniqueConstraint('provider_id', 'name',
                       name='uq_ai_model_provider_name'), )
