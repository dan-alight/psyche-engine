from pydantic import BaseModel

class AiProviderRead(BaseModel):
  id: int
  name: str
  base_url: str

  class Config:
    from_attributes = True

class AiProviderCreate(BaseModel):
  name: str
  base_url: str

class AiProviderUpdate(BaseModel):
  id: int
  name: str | None = None
  base_url: str | None = None

class ApiKeyRead(BaseModel):
  id: int
  key_value: str
  provider_id: int
  name: str
  active: bool

  class Config:
    from_attributes = True

class ApiKeyCreate(BaseModel):
  provider_id: int
  key_value: str
  name: str

class ApiKeyUpdate(BaseModel):
  provider_id: int
  key_value: str
  new_name: str | None = None
  new_active: bool | None = None
