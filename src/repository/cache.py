"""
Caching layer for repository operations.

This module provides a caching decorator and in-memory cache implementation
to improve performance of frequently accessed documents.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
import hashlib
import json

from ..core.models import BRDDocument, PRDDocument
from ..core.exceptions import DocumentNotFoundError

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU (Least Recently Used) cache implementation."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time to live for cached items in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]

            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None

            # Update access time
            self._access_times[key] = time.time()
            return value

    async def set(self, key: str, value: Any):
        """
        Set item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # If cache is full, remove least recently used item
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Find least recently used key
                lru_key = min(self._access_times, key=self._access_times.get)
                del self._cache[lru_key]
                del self._access_times[lru_key]

            # Add/update item
            self._cache[key] = (value, time.time())
            self._access_times[key] = time.time()

    async def delete(self, key: str):
        """Delete item from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_times:
                del self._access_times[key]

    async def clear(self):
        """Clear all cached items."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "oldest_access": min(self._access_times.values()) if self._access_times else None,
                "newest_access": max(self._access_times.values()) if self._access_times else None
            }


class CachedRepository:
    """Wrapper for repository with caching capabilities."""

    def __init__(self, repository, cache: Optional[LRUCache] = None):
        """
        Initialize cached repository.

        Args:
            repository: The underlying repository instance
            cache: Optional cache instance (creates default if not provided)
        """
        self.repository = repository
        self.cache = cache or LRUCache(max_size=100, ttl_seconds=3600)
        self._wrap_methods()

    def _generate_cache_key(self, method_name: str, *args, **kwargs) -> str:
        """Generate cache key from method name and arguments."""
        # Create a string representation of arguments
        key_parts = [method_name]

        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif hasattr(arg, 'document_id'):
                key_parts.append(arg.document_id)
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(
                    json.dumps(arg, sort_keys=True, default=str).encode()
                ).hexdigest()[:8])

        # Add kwargs
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        return ":".join(key_parts)

    def _wrap_methods(self):
        """Wrap repository methods with caching logic."""
        # Methods to cache
        cached_methods = [
            'get_brd',
            'get_prd',
            'list_brds',
            'list_prds',
            'search',
            'get_document_history'
        ]

        # Methods that invalidate cache
        invalidating_methods = {
            'save_brd': ['get_brd', 'list_brds', 'search'],
            'save_prd': ['get_prd', 'list_prds', 'search'],
            'update_brd': ['get_brd', 'list_brds', 'search'],
            'update_prd': ['get_prd', 'list_prds', 'search'],
            'delete_brd': ['get_brd', 'list_brds', 'search'],
            'delete_prd': ['get_prd', 'list_prds', 'search']
        }

        # Wrap cached methods
        for method_name in cached_methods:
            original_method = getattr(self.repository, method_name)
            wrapped_method = self._create_cached_method(method_name, original_method)
            setattr(self, method_name, wrapped_method)

        # Wrap invalidating methods
        for method_name, invalidates in invalidating_methods.items():
            original_method = getattr(self.repository, method_name)
            wrapped_method = self._create_invalidating_method(
                method_name,
                original_method,
                invalidates
            )
            setattr(self, method_name, wrapped_method)

        # Pass through other methods
        for attr_name in dir(self.repository):
            if not attr_name.startswith('_') and not hasattr(self, attr_name):
                attr = getattr(self.repository, attr_name)
                if callable(attr):
                    setattr(self, attr_name, attr)

    def _create_cached_method(self, method_name: str, original_method: Callable):
        """Create a cached version of a method."""
        @wraps(original_method)
        async def cached_method(*args, **kwargs):
            # Generate cache key
            cache_key = self._generate_cache_key(method_name, *args, **kwargs)

            # Try to get from cache
            cached_value = await self.cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Call original method
            logger.debug(f"Cache miss for {cache_key}")
            try:
                result = await original_method(*args, **kwargs)

                # Cache the result
                await self.cache.set(cache_key, result)

                return result
            except DocumentNotFoundError:
                # Don't cache not found errors
                raise

        return cached_method

    def _create_invalidating_method(
        self,
        method_name: str,
        original_method: Callable,
        invalidates: list[str]
    ):
        """Create a method that invalidates cache entries."""
        @wraps(original_method)
        async def invalidating_method(*args, **kwargs):
            # Call original method
            result = await original_method(*args, **kwargs)

            # Invalidate related cache entries
            # For simplicity, clear all cache for invalidated methods
            # In production, would be more selective
            logger.debug(f"{method_name} called, invalidating cache for {invalidates}")

            # Clear cache selectively based on document ID if available
            if args and hasattr(args[0], 'document_id'):
                document_id = args[0].document_id
                await self._invalidate_document_cache(document_id, invalidates)
            elif args and isinstance(args[0], str):
                # First arg is likely document_id
                await self._invalidate_document_cache(args[0], invalidates)
            else:
                # Clear all related caches
                await self.cache.clear()

            return result

        return invalidating_method

    async def _invalidate_document_cache(self, document_id: str, methods: list[str]):
        """Invalidate cache entries for a specific document."""
        # Generate potential cache keys to invalidate
        keys_to_delete = []

        for method in methods:
            # Direct get methods
            if method in ['get_brd', 'get_prd']:
                keys_to_delete.append(f"{method}:{document_id}")

            # For list and search methods, clear all
            # In production, would maintain index of keys
            if method in ['list_brds', 'list_prds', 'search']:
                await self.cache.clear()
                return

        # Delete specific keys
        for key in keys_to_delete:
            await self.cache.delete(key)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return await self.cache.get_stats()

    async def clear_cache(self):
        """Clear all cached items."""
        await self.cache.clear()
        logger.info("Cache cleared")


def with_cache(
    max_size: int = 100,
    ttl_seconds: int = 3600
) -> Callable:
    """
    Decorator to add caching to a repository class.

    Usage:
        @with_cache(max_size=50, ttl_seconds=1800)
        class MyRepository(FileSystemRepository):
            pass
    """
    def decorator(cls):
        """Wrap repository class with caching."""
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            # Call original init
            original_init(self, *args, **kwargs)

            # Create cache
            cache = LRUCache(max_size=max_size, ttl_seconds=ttl_seconds)

            # Wrap with CachedRepository
            cached_repo = CachedRepository(self, cache)

            # Replace methods with cached versions
            for attr_name in dir(cached_repo):
                if not attr_name.startswith('_'):
                    attr = getattr(cached_repo, attr_name)
                    if callable(attr):
                        setattr(self, attr_name, attr)

            # Store cache reference
            self._cache = cache

        cls.__init__ = new_init

        # Add cache management methods
        cls.get_cache_stats = lambda self: self._cache.get_stats()
        cls.clear_cache = lambda self: self._cache.clear()

        return cls

    return decorator