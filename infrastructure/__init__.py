"""Shared infrastructure with no business-domain knowledge."""

from .sqlite import SQLiteRepository, default_db_path

__all__ = ["SQLiteRepository", "default_db_path"]
