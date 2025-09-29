"""
PATTERN: Repository Pattern
USE WHEN: You need to decouple business logic from data access layer, implement caching/logging at data layer
KEY CONCEPTS:
- Abstraction layer hiding data storage details
- Async-first implementation for FastAPI
- Generic base class for common CRUD operations
- Domain model translation between persistence and business formats
"""
# Source: https://python.plainenglish.io/python-backend-project-advanced-setup-fastapi-example-7b7e73a52aec

import abc
from typing import Any, AsyncGenerator, Generic, Type, TypeVar
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Placeholder for SQLAlchemy model base
class Base:
    id: Any

SQLAlchemyModel = TypeVar("SQLAlchemyModel", bound=Base)
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)

class AbstractRepository(abc.ABC, Generic[SQLAlchemyModel, PydanticModel]):
    """Abstract interface for a repository."""

    @abc.abstractmethod
    async def get_by_id(self, id: Any) -> PydanticModel | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def save(self, data: PydanticModel) -> PydanticModel:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> AsyncGenerator[PydanticModel, None]:
        raise NotImplementedError