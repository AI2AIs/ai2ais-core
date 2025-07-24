# app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 3001
    WS_PORT: int = 3002
    
    # Database 
    DATABASE_URL: str = "postgresql://a2ais_user:a2ais_password@localhost:5432/a2ais_db"
    REDIS_URL: str = ""
    
    # Media
    GOOGLE_TTS_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
    TTS_PROVIDER: str = "chatterbox"
    VOICE_REFERENCES_PATH: str = "data/voices/"

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # AI APIs 
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""    


    # Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "a2ais_memories"
    
    # Embeddings
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI model
    EMBEDDING_DIMENSION: int = 1536  # text-embedding-3-small size
    
    # Memory Behavior
    MEMORY_RETENTION_DAYS: int = 30  # Keep memories for 30 days
    MAX_MEMORIES_PER_QUERY: int = 5  # Max memories to recall
    MEMORY_SIMILARITY_THRESHOLD: float = 0.7  # Similarity score threshold
    
    # Performance
    MEMORY_CACHE_SIZE: int = 100  # Recent memories in RAM
    MEMORY_BATCH_SIZE: int = 10   # Batch processing size

    # Database 
    DATABASE_URL: str = "postgresql://localhost:5432/a2ais"
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()