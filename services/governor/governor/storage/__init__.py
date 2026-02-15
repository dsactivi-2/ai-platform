"""Storage backends for governance data."""

from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage

__all__ = ["StorageBackend", "InMemoryStorage"]

# MongoDB is optional dependency
try:
    from governor.storage.mongodb import MongoDBStorage

    __all__.append("MongoDBStorage")
except ImportError:
    pass
