from typing import Type, cast

from fastapi import Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from fastcrud.endpoint.endpoint_creator import EndpointCreator
from fastcrud.endpoint.helper import _apply_model_pk
from fastcrud.exceptions.http_exceptions import NotFoundException

class CustomEndpointCreator(EndpointCreator):

  def _update_item(self):
    """Creates an endpoint for updating an existing item in the database."""

    @_apply_model_pk(**self._primary_keys_types)  # type: ignore
    async def endpoint(
        item: self.update_schema = Body(...),  # type: ignore
        db: AsyncSession = Depends(self.session),
        **pkeys,
    ):
      return await self.crud.update(
          db,
          item,
          return_as_model=True,
          schema_to_select=self.select_schema,
          **pkeys)

    return endpoint
