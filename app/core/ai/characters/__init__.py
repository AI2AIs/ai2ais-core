# app/core/ai/characters/__init__.py - Updated with Memory
"""
A2AIs Character System with Memory Integration

This module provides AI characters with distinct personalities, memory capabilities,
and relationship dynamics for autonomous debates.
"""

from .claude import ClaudeCharacter
from .gpt import GPTCharacter  
from .grok import GrokCharacter
from .memory_enhanced_base import MemoryEnhancedBaseCharacter

# Character registry with memory-enhanced characters
CHARACTERS = {
    "claude": ClaudeCharacter,
    "gpt": GPTCharacter,
    "grok": GrokCharacter
}

def get_character(character_id: str) -> MemoryEnhancedBaseCharacter:
    """Get a memory-enhanced character instance"""
    
    if character_id not in CHARACTERS:
        raise ValueError(f"Unknown character: {character_id}. Available: {list(CHARACTERS.keys())}")
    
    character_class = CHARACTERS[character_id]
    character_instance = character_class()
    
    print(f"🤖 Created memory-enhanced {character_id} character")
    return character_instance

def get_available_characters() -> list:
    """Get list of available character IDs"""
    return list(CHARACTERS.keys())

# Version info
__version__ = '2.0.0'  # Memory-enhanced version
__author__ = 'A2AIs Team'

__all__ = [
    'ClaudeCharacter',
    'GPTCharacter', 
    'GrokCharacter',
    'MemoryEnhancedBaseCharacter',
    'get_character',
    'get_available_characters'
]