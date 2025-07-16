from pydantic import BaseModel, ConfigDict

class AiProviderRead(BaseModel):
  id: int
  name: str
  base_url: str

  model_config = ConfigDict(from_attributes=True)

class AiProviderCreate(BaseModel):
  name: str
  base_url: str

class AiProviderUpdate(BaseModel):
  name: str | None = None
  base_url: str | None = None

class ApiKeyRead(BaseModel):
  id: int
  key_value: str
  provider_id: int
  name: str
  active: bool

  model_config = ConfigDict(from_attributes=True)

class ApiKeyCreate(BaseModel):
  provider_id: int
  key_value: str
  name: str

class ApiKeyUpdate(BaseModel):
  new_name: str | None = None
  new_active: bool | None = None

class AiModelRead(BaseModel):
  id: int
  name: str
  provider_id: int
  active: bool

  model_config = ConfigDict(from_attributes=True)

class AiModelUpdate(BaseModel):
  active: bool | None = None