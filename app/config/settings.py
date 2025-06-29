# # app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 3001
    WS_PORT: int = 3002
    
    # Database 
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    
    # Media
    GOOGLE_TTS_API_KEY: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # AI APIs 
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()