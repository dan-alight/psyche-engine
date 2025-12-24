from enum import Enum
from typing import Type, TypeVar, Literal
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.types import Integer
from psyche.models.mixins import IDMixin
from psyche.fastapi_deps import SessionDep

ModelType = TypeVar("ModelType", bound=IDMixin)
AllowedMethods = Literal["read_all", "read_one", "create", "update", "delete"]

def add_crud_routes(
    *,
    router: APIRouter,
    model: Type[ModelType],
    read_schema: Type[BaseModel] | None = None,
    create_schema: Type[BaseModel] | None = None,
    update_schema: Type[BaseModel] | None = None,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    methods: list[AllowedMethods] = [
        "read_all", "read_one", "create", "update", "delete"
    ],
    url_param_to_field: dict[str, str] = {},
    query_param_to_field: dict[str, str] = {},
) -> None:

  def get_typed_value(raw_val: str, column):
    if isinstance(column.type, Integer):
      return int(raw_val)
    return raw_val

  if "read_all" in methods and read_schema is not None:

    @router.get(f"{prefix}", response_model=list[read_schema], tags=tags)
    async def read_all(
        request: Request,
        db: SessionDep,
        skip: int = 0,
        limit: int | None = None):
      stmt = select(model)

      for url_param, field_name in url_param_to_field.items():
        raw_val = request.path_params[url_param]
        column = getattr(model, field_name)
        stmt = stmt.where(column == get_typed_value(raw_val, column))

      for query_param, field_name in query_param_to_field.items():
        raw_val = request.query_params.get(query_param)
        if raw_val is not None:
          column = getattr(model, field_name)
          stmt = stmt.where(column == get_typed_value(raw_val, column))

      stmt = stmt.offset(skip)
      if limit is not None:
        stmt = stmt.limit(limit)

      result = await db.scalars(stmt)
      return result.all()

  if "read_one" in methods and read_schema is not None:

    @router.get(f"{prefix}/{{id}}", response_model=read_schema, tags=tags)
    async def read_one(id: int, db: SessionDep):
      item = await db.get(model, id)
      if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
      return item

  if "create" in methods and create_schema is not None:

    @router.post(f"{prefix}", response_model=read_schema, tags=tags)
    async def create(request: Request, item: BaseModel, db: SessionDep):
      item_data = item.model_dump()

      for url_param, field_name in url_param_to_field.items():
        raw_val = request.path_params[url_param]
        column = getattr(model, field_name)
        if isinstance(column.type, Integer):
          item_data[field_name] = int(raw_val)
        else:
          item_data[field_name] = raw_val

      db_item = model(**item_data)
      db.add(db_item)
      await db.commit()
      await db.refresh(db_item)
      return db_item

    create.__annotations__["item"] = create_schema

  if "update" in methods and update_schema is not None:

    @router.patch(f"{prefix}/{{id}}", response_model=read_schema, tags=tags)
    async def update(id: int, item: BaseModel, db: SessionDep):
      db_item = await db.get(model, id)
      if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
      for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

      await db.commit()
      await db.refresh(db_item)
      return db_item

    update.__annotations__["item"] = update_schema

  if "delete" in methods:

    @router.delete(f"{prefix}/{{id}}", tags=tags)
    async def delete(id: int, db: SessionDep):
      db_item = await db.get(model, id)
      if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
      await db.delete(db_item)
      await db.commit()
      return {"message": "Item deleted"}
