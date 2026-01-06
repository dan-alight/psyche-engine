from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from psyche.database import SessionLocal
from psyche.models.openai_api_models import OpenAiApiKey
from psyche.exceptions import ResourceNotFoundError

clients: dict[int, AsyncOpenAI] = {}

async def get_openai_client(pid: int) -> AsyncOpenAI:
  async with SessionLocal() as db:
    api_key = await db.scalar(
        select(OpenAiApiKey).options(selectinload(OpenAiApiKey.provider)).where(
            OpenAiApiKey.provider_id == pid, OpenAiApiKey.active))
    if not api_key:
      raise ResourceNotFoundError()
    provider = api_key.provider

  client = clients.get(pid, None)

  if isinstance(
      client, AsyncOpenAI
  ) and client.base_url == provider.base_url and client.api_key == api_key.key:
    return client

  new_client = AsyncOpenAI(base_url=provider.base_url, api_key=api_key.key)
  clients[pid] = new_client
  return new_client
