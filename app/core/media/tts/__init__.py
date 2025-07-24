# app/core/media/tts/__init__.py
from app.config.settings import settings

def get_tts_service():
    """TTS service factory"""
    if settings.TTS_PROVIDER == "chatterbox":
        from .chatterbox_tts import autonomous_chatterbox_service
        return autonomous_chatterbox_service
    else:
        from .google_tts import tts_service  
        return tts_service

# Global service instance
tts_service = get_tts_service()