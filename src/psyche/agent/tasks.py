from datetime import datetime
from psyche.schemas.chat_schemas import ConversationMessageRead, ConversationMessageCreate
from psyche.models.chat_models import ConversationMessageRole

async def f(chat_message_create: ConversationMessageCreate):
  conversation_message_read = ConversationMessageRead(
      id=0,
      conversation_id=0,
      parent_message_id=0,
      role=ConversationMessageRole.USER.value,
      content=chat_message_create.content,
      created_at=datetime.now())
  return conversation_message_read
