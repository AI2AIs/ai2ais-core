# app/core/memory/__init__.py
"""
A2AIs Memory System

This module provides persistent memory capabilities for AI characters,
enabling them to remember past conversations, build relationships,
and develop expertise over time.

Components:
- EmbeddingService: Converts text to vector embeddings
- MemoryVectorStore: Stores and retrieves memories using Qdrant
- CharacterMemoryManager: Per-character memory management
"""

from .embeddings import embedding_service, EmbeddingService
from .vector_store import vector_store, MemoryVectorStore  
from .character_memory import CharacterMemoryManager, ConversationMemory, RelationshipPattern

__all__ = [
    'embedding_service',
    'EmbeddingService',
    'vector_store', 
    'MemoryVectorStore',
    'CharacterMemoryManager',
    'ConversationMemory',
    'RelationshipPattern'
]

# Version info
__version__ = '1.0.0'
__author__ = 'A2AIs Team'