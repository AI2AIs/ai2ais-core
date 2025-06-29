# app/core/media/tts/voice_profiles.py
from typing import Dict, Any

# Character voice configurations
CHARACTER_VOICES = {
    "claude": {
        "provider": "google",
        "config": {
            "name": "en-US-Neural2-A",  # Professional, thoughtful male voice
            "ssmlGender": "MALE",
            "languageCode": "en-US",
            "speakingRate": 0.9,        # Slightly slower, thoughtful
            "pitch": -2.0               # Slightly deeper
        }
    },
    "gpt": {
        "provider": "google", 
        "config": {
            "name": "en-US-Neural2-F",  # Enthusiastic, creative female voice
            "ssmlGender": "FEMALE",
            "languageCode": "en-US",
            "speakingRate": 1.1,        # Slightly faster, energetic
            "pitch": 2.0                # Slightly higher
        }
    },
    "grok": {
        "provider": "google",
        "config": {
            "name": "en-US-Neural2-D",  # Direct, confident male voice
            "ssmlGender": "MALE", 
            "languageCode": "en-US",
            "speakingRate": 1.0,        # Normal speed, direct
            "pitch": 0.0                # Normal pitch
        }
    }
}

def get_voice_config(character_id: str) -> Dict[str, Any]:
    """Get voice configuration for character"""
    return CHARACTER_VOICES.get(character_id, CHARACTER_VOICES["claude"])