from psyche.schemas.chat_schemas import ChatMessageRead, ChatMessageCreate

async def f(chat_message_create: ChatMessageCreate):
  chat_message_read = ChatMessageRead(
      id=0, conversation_id=0, content=chat_message_create.content)
  return chat_message_read
