from sqlalchemy import select
from psyche.models.openai_api_models import AiProvider, ApiKey
from psyche.exceptions import ResourceNotFoundError, InvalidStateError
from openai import AsyncOpenAI
from psyche.database import SessionLocal

openai_client_cache = {}

async def get_openai_client(provider_id: int) -> AsyncOpenAI:
  async with SessionLocal() as db:
    provider = await db.get(AiProvider, provider_id)
    if not provider:
      raise ResourceNotFoundError(
          resource_type="AiProvider", resource_id=provider_id)

    active_api_key = await db.scalar(
        select(ApiKey).where(
            ApiKey.provider_id == provider_id, ApiKey.active == True))
    if not active_api_key:
      raise InvalidStateError(
          f"No active API key found for provider ID {provider_id}")

  cached_client, cached_base_url, cached_api_key = openai_client_cache.get(
      provider_id, (None, None, None))

  if (cached_client and cached_base_url == provider.base_url
      and cached_api_key == active_api_key.key_value):
    return cached_client

  new_client = AsyncOpenAI(
      base_url=provider.base_url,
      api_key=active_api_key.key_value,
  )
  openai_client_cache[provider_id] = (
      new_client, provider.base_url, active_api_key.key_value)

  return new_client
