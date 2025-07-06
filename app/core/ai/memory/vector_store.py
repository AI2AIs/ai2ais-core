# app/core/ai/memory/vector_store.py
import asyncio
import logging
from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
import time
import uuid

from app.config.settings import settings

logger = logging.getLogger(__name__)

class VectorStoreError(Exception):
    """Vector store operation failed"""
    pass

class MemoryVectorStore:
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        
        self.client: Optional[QdrantClient] = None
        self._connection_verified = False
        
    async def _ensure_connection(self):
        """Ensure Qdrant connection is established"""
        if self.client and self._connection_verified:
            return True
            
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            
            # Test connection
            collections = self.client.get_collections()
            self._connection_verified = True
            
            logger.info(f"✅ Connected to Qdrant at {self.host}:{self.port}")
            await self._ensure_collection()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            self.client = None
            self._connection_verified = False
            return False
    
    async def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        if not self.client:
            return
            
        try:
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"✅ Collection '{self.collection_name}' exists")
            
        except Exception:
            try:
                from qdrant_client.models import VectorParams, Distance
                
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"✅ Recreated collection '{self.collection_name}'")
                
            except Exception as e:
                logger.error(f"❌ Collection creation failed: {e}")
                raise VectorStoreError(f"Failed to create collection: {e}")
    
    async def store_memory(self, memory_data: Dict) -> bool:
        """Store a memory in the vector database - FAIL FAST"""
        
        if not await self._ensure_connection():
            raise VectorStoreError("Qdrant unavailable - cannot store memory")
        
        try:
            from qdrant_client.models import PointStruct
            
            # Extract and validate data
            memory_id = str(memory_data["id"])
            vector = memory_data["vector"]
            metadata = memory_data["metadata"]
            
            # Vector validation - FAIL FAST
            if not isinstance(vector, list):
                raise VectorStoreError(f"Vector must be list, got {type(vector)}")
            
            vector = [float(x) for x in vector]
            
            if len(vector) != self.dimension:
                raise VectorStoreError(f"Vector dimension mismatch: {len(vector)} vs {self.dimension}")
            
            # Create and store point
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload=metadata
            )
            
            operation_result = self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"✅ Memory stored successfully: {memory_id}")
            return True
            
        except VectorStoreError:
            raise  # Re-raise our custom errors
        except Exception as e:
            logger.error(f"❌ Failed to store memory {memory_data.get('id', 'unknown')}: {e}")
            raise VectorStoreError(f"Failed to store memory: {e}")
    
    async def search_memories(self, 
                            query_vector: List[float],
                            character_id: str = None,
                            topic: str = None,
                            emotion: str = None,
                            limit: int = 5,
                            score_threshold: float = None) -> List[Dict]:
        """Search for similar memories - FAIL FAST"""
        
        if not await self._ensure_connection():
            raise VectorStoreError("Qdrant unavailable - cannot search memories")
        
        try:
            # Build filter conditions
            must_conditions = []
            
            if character_id:
                must_conditions.append(
                    FieldCondition(
                        key="character_id",
                        match=MatchValue(value=character_id)
                    )
                )
            
            if topic:
                must_conditions.append(
                    FieldCondition(
                        key="topic",
                        match=MatchValue(value=topic)
                    )
                )
            
            if emotion:
                must_conditions.append(
                    FieldCondition(
                        key="emotion", 
                        match=MatchValue(value=emotion)
                    )
                )
            
            search_filter = Filter(must=must_conditions) if must_conditions else None
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "memory": result.payload,
                    "id": result.id
                })
            
            logger.info(f"🔍 Found {len(formatted_results)} similar memories")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Memory search failed: {e}")
            raise VectorStoreError(f"Failed to search memories: {e}")
    
    async def get_character_memory_count(self, character_id: str) -> int:
        """Get total memory count for a character - FAIL FAST"""
        
        if not await self._ensure_connection():
            raise VectorStoreError("Qdrant unavailable - cannot count memories")
        
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
            
        except Exception as e:
            logger.error(f"❌ Failed to count memories: {e}")
            raise VectorStoreError(f"Failed to count memories: {e}")
    
    async def test_connection(self) -> bool:
        """Test vector store connection"""
        try:
            return await self._ensure_connection()
        except Exception:
            return False

# Global instance
vector_store = MemoryVectorStore()