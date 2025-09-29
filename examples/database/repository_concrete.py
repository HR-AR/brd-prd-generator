"""
PATTERN: Repository Pattern - Concrete Implementation
USE WHEN: Implementing specific data access logic with SQLAlchemy
KEY CONCEPTS:
- Session management
- Translation between SQLAlchemy and Pydantic models
- Memory-efficient streaming with AsyncGenerator
"""
# Source: https://python.plainenglish.io/python-backend-project-advanced-setup-fastapi-example-7b7e73a52aec

from typing import Any, AsyncGenerator, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from .repository_base import AbstractRepository, SQLAlchemyModel, PydanticModel

class SQLAlchemyRepository(AbstractRepository[SQLAlchemyModel, PydanticModel]):
    """
    Generic SQLAlchemy repository implementation.
    Manages the session and translation between SQLAlchemy and Pydantic models.
    """

    def __init__(
        self,
        session: AsyncSession,
        sql_model: Type[SQLAlchemyModel],
        pydantic_model: Type[PydanticModel],
    ):
        self._session = session
        self._sql_model = sql_model
        self._pydantic_model = pydantic_model

    async def get_by_id(self, id: Any) -> PydanticModel | None:
        stmt = select(self._sql_model).where(self._sql_model.id == id)
        result = await self._session.execute(stmt)
        instance = result.scalars().one_or_none()
        return self._pydantic_model.model_validate(instance) if instance else None

    async def save(self, data: PydanticModel) -> PydanticModel:
        # In a real implementation, handle create vs. update logic
        instance = self._sql_model(**data.model_dump())
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return self._pydantic_model.model_validate(instance)

    async def list_all(self) -> AsyncGenerator[PydanticModel, None]:
        stmt = select(self._sql_model)
        result = await self._session.stream_scalars(stmt)
        async for instance in result:
            yield self._pydantic_model.model_validate(instance)