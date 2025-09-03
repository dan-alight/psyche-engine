from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.inspection import inspect

class Base(DeclarativeBase):
  @classmethod
  def fields(cls) -> set[str]:
    return {c.key for c in inspect(cls).mapper.column_attrs}
