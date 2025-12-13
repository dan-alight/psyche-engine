from pydantic import BaseModel, ConfigDict

class OpenAiApiProviderRead(BaseModel):
  id: int
  name: str
  base_url: str

  model_config = ConfigDict(from_attributes=True)

class OpenAiApiProviderCreate(BaseModel):
  name: str
  base_url: str

class OpenAiApiProviderUpdate(BaseModel):
  name: str | None = None
  base_url: str | None = None

class OpenAiApiKeyRead(BaseModel):
  id: int
  key: str
  provider_id: int
  active: bool

  model_config = ConfigDict(from_attributes=True)

class OpenAiApiKeyCreate(BaseModel):
  key: str
  active: bool = True

class OpenAiApiKeyUpdate(BaseModel):
  key: str | None = None
  provider_id: int | None = None
  active: bool | None = None

class OpenAiApiModelRead(BaseModel):
  id: int
  name: str
  provider_id: int
  bookmarked: bool

  model_config = ConfigDict(from_attributes=True)

class OpenAiApiModelCreate(BaseModel):
  name: str
  bookmarked: bool = False

class OpenAiApiModelUpdate(BaseModel):
  name: str | None = None
  provider_id: int | None = None
  bookmarked: bool | None = None
