from datetime import datetime
from psyche.models.base import Base
from sqlalchemy import Integer, String, DateTime, text, ForeignKey, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

class Conversation(Base):
  __tablename__ = "conversation"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  title: Mapped[str] = mapped_column(String)
  last_updated: Mapped[datetime | None] = mapped_column(DateTime)

class ConversationMessage(Base):
  __tablename__ = "conversation_message"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  conversation_id: Mapped[int] = mapped_column(
      Integer, ForeignKey("conversation.id", ondelete="CASCADE"), index=True)
  parent_message_id: Mapped[int | None] = mapped_column(Integer)
  content: Mapped[str] = mapped_column(String)
  created_at: Mapped[datetime] = mapped_column(
      DateTime, server_default=text("CURRENT_TIMESTAMP"))

  __table_args__ = (
      UniqueConstraint(
          "id", "conversation_id", name="uq_message_id_conversation_id"),
      ForeignKeyConstraint(
          ["parent_message_id", "conversation_id"],
          ["conversation_message.id", "conversation_message.conversation_id"],
          name="fk_parent_message_same_conversation",
          ondelete="CASCADE",
      ),
  )
