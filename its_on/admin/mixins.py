from typing import Dict, Union

from sqlalchemy.engine import ResultProxy
from sqlalchemy import Table
from aiohttp.web import Request
from marshmallow import Schema
from multidict import MultiDictProxy, MultiDict


class GetObjectMixin:
    model: Table

    async def get_object_pk(self, request: Request) -> str:
        return request.match_info.get('id')

    async def get_object(self, request: Request) -> ResultProxy:
        async with request.app['db'].acquire() as conn:
            object_id = await self.get_object_pk(request)
            query = self.model.select(self.model.c.id == object_id)

            result = await conn.execute(query)
            return await result.fetchone()


class UpdateMixin(GetObjectMixin):
    model: Table
    validator: Schema

    async def update_object(self, request: Request, to_update: Union[MultiDictProxy, MultiDict]) -> None:
        validated_data = self._validate_form_data(to_update)

        await self._update(request, validated_data)

    async def _update(self, request: Request, to_update: Dict[str, Union[str, bool, int]]) -> None:
        async with request.app['db'].acquire() as conn:
            object_pk = await self.get_object_pk(request)
            update_query = self.model.update().where(self.model.c.id == object_pk).values(to_update)

            await conn.execute(update_query)

    def _validate_form_data(self, to_validate: Union[MultiDictProxy, MultiDict]) -> Dict[str, Union[int, str, bool]]:
        return self.validator.load(to_validate)


class CreateMixin:
    model: Table
    validator: Schema

    async def create_object(self, request: Request, to_create: MultiDictProxy) -> None:
        validated_data = self._validate_form_data(to_create)
        validated_data['name'] = str(validated_data['name']).strip()
        await self._create(request, validated_data)

    async def _create(self, request: Request, to_create: Dict[str, Union[str, bool, int]]) -> None:
        async with request.app['db'].acquire() as conn:
            create_query = self.model.insert().values(to_create)

            await conn.execute(create_query)

    def _validate_form_data(self, to_validate: MultiDictProxy) -> Dict[str, Union[int, str, bool]]:
        return self.validator.load(to_validate)
