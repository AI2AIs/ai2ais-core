from .claude import ClaudeCharacter
from .gpt import GPTCharacter  
from .grok import GrokCharacter

# Character registry
CHARACTERS = {
    "claude": ClaudeCharacter,
    "gpt": GPTCharacter,
    "grok": GrokCharacter
}

def get_character(character_id: str):
    """Get character instance by ID"""
    character_class = CHARACTERS.get(character_id)
    if character_class:
        return character_class()
    raise ValueError(f"Unknown character: {character_id}")

def get_available_characters():
    """Get list of available character IDs"""
    return list(CHARACTERS.keys())