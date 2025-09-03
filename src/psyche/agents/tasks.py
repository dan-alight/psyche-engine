import asyncio
import logging
from typing import cast
from datetime import datetime
from sqlalchemy import select, delete, update, func
from psyche.schemas.chat_schemas import ConversationMessageRead, ConversationMessageCreate, ConversationMessagePart, GenerateReplyToExistingMessage, ChatRequest
from psyche.models.chat_models import ConversationMessageRole, ConversationMessage
from psyche.models.ai_models import AiModel
from psyche.database import SessionLocal, get_session
from psyche.exceptions import InvalidStateError
from psyche.openai_clients import get_openai_client
from openai.types.chat import ChatCompletionMessageParam

logger = logging.getLogger("psyche.agents")

async def stream_chat(chat_request: ChatRequest):

  match chat_request.action:
    case ConversationMessageCreate():
      user_message = ConversationMessage(
          **chat_request.action.model_dump(exclude={"type"}),
          role=ConversationMessageRole.USER)

      async with SessionLocal() as db:
        db.add(user_message)
        await db.commit()
        await db.refresh(user_message)

      conversation_id = user_message.conversation_id

      yield ConversationMessageRead.model_validate(user_message).model_dump(
          mode="json")

    case GenerateReplyToExistingMessage():
      async with SessionLocal() as db:
        existing_message = await db.get(
            ConversationMessage, chat_request.action.existing_message_id)
      if not existing_message:
        raise InvalidStateError(
            f"Message with ID {chat_request.action.existing_message_id} not found."
        )
      conversation_id = existing_message.conversation_id

  # Send the chat history via OpenAI API

  # Fetch all messages in the conversation to provide context
  async with SessionLocal() as db:
    result = await db.execute(
        select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id).order_by(
                ConversationMessage.id))
    messages = result.scalars().all()

    # Validate the config and extract provider-specific settings
    config = chat_request.config
    logger.info(f"Chat config: {config}")
    ai_model_id = config.get("ai_model_id")
    if not ai_model_id:
      raise InvalidStateError("AI model ID must be specified in config.")
    result = await db.execute(select(AiModel).where(AiModel.id == ai_model_id))
    ai_model = result.scalar_one_or_none()
    if not ai_model or not ai_model.active:
      raise InvalidStateError(
          f"AI model with ID {ai_model_id} not found or inactive.")

  # Convert messages to the format required by the provider
  # This assumes there is no branching in the conversation history
  formatted_messages = [
      cast(
          ChatCompletionMessageParam,
          {
              "role": msg.role.value,
              "content": msg.content,
          },
      ) for msg in messages
  ]

  client = await get_openai_client(ai_model.provider_id)
  completion = await client.chat.completions.create(
      model=ai_model.name, messages=formatted_messages)

  # Store the assistant's reply in the database
  assistant_message = ConversationMessage(
      conversation_id=conversation_id,
      content=completion.choices[0].message.content,
      role=ConversationMessageRole.ASSISTANT)
  async with SessionLocal() as db:
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

  yield ConversationMessageRead.model_validate(assistant_message).model_dump(
      mode="json")
