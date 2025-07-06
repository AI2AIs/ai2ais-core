# app/core/database/__init__.py
"""
A2AIs Database Package
PostgreSQL persistence layer for character evolution and session tracking
"""

from .service import db_service, DatabaseService

__all__ = [
    'db_service',
    'DatabaseService'
]

__version__ = '1.0.0'