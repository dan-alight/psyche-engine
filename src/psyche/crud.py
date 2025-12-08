import logging
from typing import Type, TypeVar
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from psyche.models.mixins import IDMixin
from psyche.fastapi_deps import SessionDep

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=IDMixin)

def add_crud_routes(
    router: APIRouter, model_class: Type[ModelType],
    read_schema: Type[BaseModel], create_schema: Type[BaseModel],
    update_schema: Type[BaseModel]):

  @router.get("", response_model=list[read_schema])
  async def read_all(db: SessionDep, skip: int = 0, limit: int = 100):
    stmt = select(model_class).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

  @router.get("/{id}", response_model=read_schema)
  async def read_one(id: int, db: SessionDep):
    stmt = select(model_class).where(model_class.id == id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if item is None:
      raise HTTPException(status_code=404, detail="Item not found")
    return item

  @router.post("", response_model=read_schema)
  async def create(request: BaseModel, db: SessionDep):
    db_item = model_class(**request.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

  create.__annotations__["request"] = create_schema

  @router.patch("/{id}", response_model=read_schema)
  async def update(id: int, request: BaseModel, db: SessionDep):
    stmt = select(model_class).where(model_class.id == id)
    result = await db.execute(stmt)
    db_item = result.scalar_one_or_none()
    if db_item is None:
      raise HTTPException(status_code=404, detail="Item not found")
    for key, value in request.model_dump(exclude_unset=True).items():
      setattr(db_item, key, value)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

  update.__annotations__["request"] = update_schema

  @router.delete("/{id}")
  async def delete(id: int, db: SessionDep):
    stmt = select(model_class).where(model_class.id == id)
    result = await db.execute(stmt)
    db_item = result.scalar_one_or_none()
    if db_item is None:
      raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(db_item)
    await db.commit()
    return {"message": "Item deleted"}
