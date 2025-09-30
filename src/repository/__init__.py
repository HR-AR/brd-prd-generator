"""
Repository module for document storage and retrieval.
"""

from .base import BaseRepository
from .filesystem import FileSystemRepository
from .cache import (
    LRUCache,
    CachedRepository,
    with_cache
)

__all__ = [
    'BaseRepository',
    'FileSystemRepository',
    'LRUCache',
    'CachedRepository',
    'with_cache'
]

# Create default cached repository
@with_cache(max_size=100, ttl_seconds=3600)
class CachedFileSystemRepository(FileSystemRepository):
    """File system repository with built-in caching."""
    pass


def get_repository(
    repository_type: str = "filesystem",
    base_path: str = "./data/documents",
    use_cache: bool = True,
    cache_size: int = 100,
    cache_ttl: int = 3600
) -> BaseRepository:
    """
    Factory function to get a repository instance.

    Args:
        repository_type: Type of repository ("filesystem", etc.)
        base_path: Base path for file storage
        use_cache: Whether to use caching
        cache_size: Maximum cache size
        cache_ttl: Cache TTL in seconds

    Returns:
        Repository instance

    Raises:
        ValueError: If repository type is not supported
    """
    if repository_type == "filesystem":
        if use_cache:
            # Create cached repository
            repo = FileSystemRepository(base_path)
            cache = LRUCache(max_size=cache_size, ttl_seconds=cache_ttl)
            return CachedRepository(repo, cache)
        else:
            # Create uncached repository
            return FileSystemRepository(base_path)
    else:
        raise ValueError(f"Unsupported repository type: {repository_type}")


# Export factory function
__all__.append('get_repository')
__all__.append('CachedFileSystemRepository')