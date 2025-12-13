from openai import AsyncOpenAI
from fastapi import HTTPException
from sqlalchemy import select
from psyche.database import SessionLocal
from psyche.models.openai_api_models import OpenAiApiProvider, OpenAiApiKey

clients: dict[int, AsyncOpenAI] = {}

async def get_openai_client(provider_id: int) -> AsyncOpenAI:
  async with SessionLocal() as db:
    result = await db.execute(
        select(OpenAiApiKey).where(
            OpenAiApiKey.provider_id == provider_id, OpenAiApiKey.active))
    api_key = result.scalar_one_or_none()
    if not api_key:
      raise HTTPException(status_code=404, detail="No active api key")

  provider = api_key.provider
  client = clients.get(provider_id, None)

  if isinstance(
      client, AsyncOpenAI
  ) and client.base_url == provider.base_url and client.api_key == api_key.key:
    return client

  new_client = AsyncOpenAI(base_url=provider.base_url, api_key=api_key.key)
  clients[provider_id] = new_client
  return new_client
