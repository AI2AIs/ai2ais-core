# app/core/ai/memory/vector_store.py - SIMPLE QDRANT FORMAT
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
            logger.warning("Will use mock vector store for development")
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
                
                # ✅ Recreate with proper params
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
                raise
    
    async def store_memory(self, memory_data: Dict) -> bool:
        """Store a memory in the vector database"""
        
        if not await self._ensure_connection():
            logger.warning("Qdrant not available, storing in mock store")
            return await self._store_memory_mock(memory_data)
        
        try:
            # ✅ Import at method level to avoid circular imports
            from qdrant_client.models import PointStruct
            
            # ✅ Extract and validate data
            memory_id = str(memory_data["id"])
            vector = memory_data["vector"]
            metadata = memory_data["metadata"]
            
            # ✅ Vector validation
            if not isinstance(vector, list):
                logger.error(f"❌ Vector must be list, got {type(vector)}")
                return await self._store_memory_mock(memory_data)
            
            # Ensure all values are floats
            vector = [float(x) for x in vector]
            
            if len(vector) != self.dimension:
                logger.error(f"❌ Vector dimension mismatch: {len(vector)} vs {self.dimension}")
                return await self._store_memory_mock(memory_data)
            
            # ✅ Create point using PointStruct
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload=metadata
            )
            
            # ✅ Debug logging
            logger.debug(f"🔍 Storing point: ID={memory_id}")
            logger.debug(f"🔍 Vector: len={len(vector)}, sample={vector[:3]}")
            logger.debug(f"🔍 Payload keys: {list(metadata.keys())}")
            
            # ✅ Store using upsert
            operation_result = self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.info(f"✅ Memory stored successfully: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store memory {memory_data.get('id', 'unknown')}: {e}")
            logger.error(f"🔍 Error type: {type(e)}")
            
            # ✅ Detailed error info
            if hasattr(e, 'status_code'):
                logger.error(f"🔍 HTTP Status: {e.status_code}")
            if hasattr(e, 'content'):
                logger.error(f"🔍 Response: {e.content}")
                
            # Log the exact data that failed
            logger.error(f"🔍 Failed data - ID: {memory_data.get('id')}")
            logger.error(f"🔍 Failed data - Vector type: {type(memory_data.get('vector'))}")
            logger.error(f"🔍 Failed data - Vector len: {len(memory_data.get('vector', []))}")
            
            # Fallback to mock storage
            return await self._store_memory_mock(memory_data)
    
    async def search_memories(self, 
                            query_vector: List[float],
                            character_id: str = None,
                            topic: str = None,
                            emotion: str = None,
                            limit: int = 5,
                            score_threshold: float = None) -> List[Dict]:
        """Search for similar memories"""
        
        if not await self._ensure_connection():
            logger.warning("Qdrant not available, using mock search")
            return await self._search_memories_mock(query_vector, character_id, topic, limit)
        
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
            
            # Create filter
            search_filter = Filter(must=must_conditions) if must_conditions else None
            
            # Search with simpler parameters
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
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
            return []
    
    async def get_character_memory_count(self, character_id: str) -> int:
        """Get total memory count for a character"""
        
        if not await self._ensure_connection():
            return 0
        
        try:
            # Simple count without complex filters for now
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
            
        except Exception as e:
            logger.error(f"❌ Failed to count memories: {e}")
            return 0
    
    # MOCK METHODS for development without Qdrant
    
    def __init_mock_store(self):
        """Initialize mock store"""
        if not hasattr(self, '_mock_memories'):
            self._mock_memories: List[Dict] = []
    
    async def _store_memory_mock(self, memory_data: Dict) -> bool:
        """Mock memory storage"""
        self.__init_mock_store()
        
        # Store in memory list
        self._mock_memories.append({
            "id": memory_data["id"],
            "vector": memory_data["vector"],
            "payload": memory_data["metadata"]
        })
        
        logger.info(f"📝 Mock stored memory: {memory_data['id']}")
        return True
    
    async def _search_memories_mock(self, 
                                  query_vector: List[float],
                                  character_id: str = None,
                                  topic: str = None,
                                  limit: int = 5) -> List[Dict]:
        """Mock memory search"""
        self.__init_mock_store()
        
        if not self._mock_memories:
            return []
        
        # Simple filtering
        filtered_memories = []
        for memory in self._mock_memories:
            payload = memory["payload"]
            
            # Apply filters
            if character_id and payload.get("character_id") != character_id:
                continue
            if topic and payload.get("topic") != topic:
                continue
                
            filtered_memories.append(memory)
        
        # Simple scoring
        scored_memories = []
        for memory in filtered_memories[:limit]:
            mock_score = 0.8 + (hash(memory["id"]) % 20) / 100
            
            scored_memories.append({
                "score": mock_score,
                "memory": memory["payload"],
                "id": memory["id"]
            })
        
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"🔍 Mock search found {len(scored_memories)} memories")
        return scored_memories[:limit]
    
    async def test_connection(self) -> bool:
        """Test vector store connection"""
        return await self._ensure_connection()

# Global instance
vector_store = MemoryVectorStore()