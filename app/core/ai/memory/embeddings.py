# app/core/ai/memory/embeddings.py
import asyncio
import logging
from typing import List, Dict, Optional
import hashlib
import uuid

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = None
        self.model = "text-embedding-3-small"  # Default
        self.dimension = 1536  # Default
        self._client_initialized = False
        self._embedding_cache: Dict[str, List[float]] = {}
    
    async def _ensure_client(self):
        """Initialize OpenAI client when needed"""
        if self._client_initialized:
            return
        
        try:
            # Import here to avoid circular imports
            from app.config.settings import settings
            
            self.model = settings.EMBEDDING_MODEL
            self.dimension = settings.EMBEDDING_DIMENSION
            
            if settings.OPENAI_API_KEY:
                try:
                    from openai import AsyncOpenAI
                    self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                    logger.info("✅ OpenAI client initialized")
                except Exception as e:
                    logger.warning(f"OpenAI client init failed: {e}, using mock embeddings")
                    self.client = None
            else:
                logger.info("No OpenAI API key, using mock embeddings")
                self.client = None
                
        except Exception as e:
            logger.warning(f"Settings import failed: {e}, using defaults")
            self.client = None
        
        self._client_initialized = True
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        await self._ensure_client()
        
        if not self.client:
            return self._generate_mock_embedding(text)
        
        # Create cache key
        cache_key = hashlib.md5(f"{self.model}:{text}".encode()).hexdigest()
        
        # Check cache
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            self._embedding_cache[cache_key] = embedding
            
            # Manage cache size
            if len(self._embedding_cache) > 1000:
                keys = list(self._embedding_cache.keys())
                for key in keys[:100]:
                    del self._embedding_cache[key]
            
            logger.info(f"Real embedding generated: {len(embedding)} dims")
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return self._generate_mock_embedding(text)
    
    async def embed_conversation(self, 
                               character_id: str,
                               text: str, 
                               emotion: str,
                               topic: str,
                               timestamp: float,
                               other_participants: List[str] = None) -> Dict:
        """Embed conversation with metadata"""
        
        # Enhanced context
        enhanced_text = f"""
        Character: {character_id}
        Topic: {topic}
        Emotion: {emotion}
        Participants: {', '.join(other_participants or [])}
        Content: {text}
        """
        
        embedding = await self.embed_text(enhanced_text.strip())
        memory_id = str(uuid.uuid4())
        
        return {
            "id": memory_id,
            "vector": embedding,
            "metadata": {
                "character_id": character_id,
                "text": text,
                "emotion": emotion,
                "topic": topic,
                "timestamp": timestamp,
                "other_participants": other_participants or [],
                "text_length": len(text),
                "embedding_model": self.model
            }
        }
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding"""
        # Simple hash-based mock
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        mock_embedding = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            value = int(hex_pair, 16) / 255.0
            value = (value - 0.5) * 2  # -1 to 1
            mock_embedding.append(value)
        
        # Pad to dimension
        while len(mock_embedding) < self.dimension:
            mock_embedding.extend(mock_embedding[:self.dimension - len(mock_embedding)])
        
        mock_embedding = mock_embedding[:self.dimension]
        logger.debug(f"Generated mock embedding: {len(mock_embedding)} dims")
        return mock_embedding
    
    async def test_connection(self) -> bool:
        """Test service"""
        try:
            embedding = await self.embed_text("test")
            return len(embedding) == self.dimension
        except:
            return False

#  SAFE GLOBAL INSTANCE
embedding_service = EmbeddingService()