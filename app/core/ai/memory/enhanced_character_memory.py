# app/core/ai/memory/enhanced_character_memory.py
"""
Enhanced Character Memory Manager with Database Integration
NO TEXT DUPLICATION - Hybrid Qdrant + PostgreSQL approach
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass

from .embeddings import embedding_service
from .vector_store import vector_store
from app.core.database.service import db_service
from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Enhanced memory entry with database reference"""
    id: str
    character_id: str
    memory_type: str  # 'conversation', 'learning_event', 'relationship'
    timestamp: float
    importance_score: float
    
    # Qdrant reference (contains text + embedding)
    qdrant_id: str
    
    # Database reference (contains metrics + metadata)
    db_table: str  # 'session_speeches', 'learning_events', etc.
    db_id: str

class EnhancedCharacterMemory:
    """Enhanced memory manager with hybrid storage"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.memory_initialized = False
        
        # In-memory caches (for performance)
        self.recent_conversations: deque = deque(maxlen=settings.MEMORY_CACHE_SIZE)
        self.recent_learning_events: deque = deque(maxlen=20)
        self.relationship_cache: Dict[str, Dict] = {}
        
        # Performance tracking
        self.total_memories = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    async def initialize(self):
        """Initialize enhanced memory system"""
        if self.memory_initialized:
            return
        
        try:
            # Load character from database
            char_data = await db_service.get_character(self.character_id)
            if not char_data:
                logger.warning(f"Character {self.character_id} not found in database")
                return
            
            # Load recent memories into cache
            await self._load_recent_memories()
            
            self.memory_initialized = True
            logger.info(f"✅ Enhanced memory initialized for {self.character_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize enhanced memory: {e}")
            self.memory_initialized = True  # Continue without enhanced features
    
    async def store_conversation_memory(self, session_id: str, speech_text: str, 
                                    emotion: str, duration: float,
                                    voice_config: Dict = None, 
                                    context: Dict = None) -> str:
        """Store conversation with enhanced error recovery"""
        
        memory_id = str(uuid.uuid4())
        qdrant_success = False
        db_success = False
        
        try:
            # Step 1: Store in Qdrant with retry
            for attempt in range(2):  # 2 attempts
                try:
                    embedding = await embedding_service.embed_text(speech_text)
                    
                    qdrant_success = await vector_store.store_memory({
                        "id": memory_id,
                        "vector": embedding,
                        "metadata": {
                            "character_id": self.character_id,
                            "session_id": session_id,
                            "emotion": emotion,
                            "timestamp": time.time(),
                            "memory_type": "conversation",
                            "text": speech_text
                        }
                    })
                    
                    if qdrant_success:
                        break
                        
                except Exception as qdrant_error:
                    logger.warning(f"Qdrant attempt {attempt + 1} failed: {qdrant_error}")
                    if attempt == 1:  # Last attempt
                        logger.error(f"❌ All Qdrant attempts failed for {memory_id}")
            
            # Step 2: Store in PostgreSQL with retry
            for attempt in range(2):
                try:
                    db_success = await db_service.store_speech_metadata(
                        speech_id=memory_id,
                        session_id=session_id,
                        character_id=self.character_id,
                        emotion=emotion,
                        duration_seconds=duration,
                        voice_config=voice_config,
                        **context if context else {}
                    )
                    
                    if db_success:
                        break
                        
                except Exception as db_error:
                    logger.warning(f"PostgreSQL attempt {attempt + 1} failed: {db_error}")
                    if attempt == 1:
                        logger.error(f"❌ All PostgreSQL attempts failed for {memory_id}")
            
            # Step 3: Update character stats (best effort)
            try:
                await db_service.increment_character_stats(
                    character_id=self.character_id,
                    speeches=1
                )
            except Exception as stats_error:
                logger.warning(f"Failed to update character stats: {stats_error}")
            
            # Step 4: Add to local cache regardless
            memory_entry = MemoryEntry(
                id=memory_id,
                character_id=self.character_id,
                memory_type="conversation",
                timestamp=time.time(),
                importance_score=0.5,
                qdrant_id=memory_id,
                db_table="session_speeches",
                db_id=memory_id
            )
            
            self.recent_conversations.append(memory_entry)
            self.total_memories += 1
            
            # Determine success level
            if qdrant_success and db_success:
                logger.info(f"✅ Fully stored conversation memory: {memory_id}")
            elif qdrant_success or db_success:
                logger.warning(f"⚠️ Partially stored conversation memory: {memory_id}")
            else:
                logger.error(f"❌ Failed to store conversation memory: {memory_id}")
            
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Critical error storing conversation memory: {e}")
            return None
    
    async def store_learning_event(self,
                                 session_id: str,
                                 event_type: str,
                                 context_data: Dict,
                                 success_score: float = None,
                                 related_memory_id: str = None) -> str:
        """Store learning event"""
        
        try:
            # Create embedding from context (for similarity search)
            context_text = self._serialize_context_for_embedding(context_data)
            embedding = await embedding_service.embed_text(context_text)
            
            # Generate unique ID
            event_id = str(uuid.uuid4())
            
            # Step 1: Store in Qdrant
            qdrant_success = await vector_store.store_memory({
                "id": event_id,
                "vector": embedding,
                "metadata": {
                    "character_id": self.character_id,
                    "session_id": session_id,
                    "event_type": event_type,
                    "timestamp": time.time(),
                    "memory_type": "learning_event",
                    "text": context_text  # Serialized context
                }
            })
            
            # Step 2: Store in PostgreSQL
            db_event_id = await db_service.record_learning_event(
                character_id=self.character_id,
                session_id=session_id,
                event_type=event_type,
                context_data=context_data,
                qdrant_memory_id=event_id,  # Link to Qdrant
                success_score=success_score
            )
            
            if qdrant_success and db_event_id:
                logger.info(f"✅ Stored learning event: {event_id}")
                return event_id
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to store learning event: {e}")
            return None
    
    async def find_similar_conversations(self, current_text: str, limit: int = 5) -> List[Dict]:
        """Find similar conversations with enhanced error recovery"""
        
        try:
            # Step 1: Vector search in Qdrant
            query_embedding = await embedding_service.embed_text(current_text)
            
            similar_vectors = await vector_store.search_memories(
                query_vector=query_embedding,
                character_id=self.character_id,
                limit=limit * 2
            )
            
            if not similar_vectors:
                logger.info(f"🔍 No similar memories found for {self.character_id}")
                self.cache_misses += 1
                return []
            
            # Step 2: Get full data from PostgreSQL with error recovery
            conversation_ids = [result["id"] for result in similar_vectors[:limit]]
            full_conversations = []
            
            async with db_service.get_connection() as conn:
                for conv_id in conversation_ids:
                    try:
                        db_data = await conn.fetchrow("""
                            SELECT * FROM session_speeches 
                            WHERE id = $1
                        """, conv_id)
                        
                        if db_data:
                            # Find corresponding Qdrant data
                            qdrant_data = next(
                                (r for r in similar_vectors if r["id"] == conv_id), 
                                None
                            )
                            
                            if qdrant_data:
                                full_conversations.append({
                                    "id": conv_id,
                                    "text": qdrant_data["memory"].get("text", ""),
                                    "similarity_score": qdrant_data.get("score", 0.0),
                                    "emotion": dict(db_data).get("emotion", "neutral"),
                                    "duration": dict(db_data).get("duration_seconds", 0.0),
                                    "timestamp": dict(db_data).get("timestamp"),
                                    "voice_config": dict(db_data).get("voice_config", {})
                                })
                        
                    except Exception as conv_error:
                        logger.warning(f"Failed to get conversation {conv_id}: {conv_error}")
                        continue  # Skip this conversation, continue with others
            
            self.cache_hits += 1
            logger.info(f"🔍 Found {len(full_conversations)} similar conversations")
            return full_conversations
            
        except Exception as e:
            logger.error(f"❌ Failed to find similar conversations: {e}")
            self.cache_misses += 1
            
            # FALLBACK: Return empty list but don't crash
            return []
        

    
    async def get_relationship_patterns(self, other_character: str) -> Dict:
        """Get relationship patterns with caching"""
        
        # Check cache first
        if other_character in self.relationship_cache:
            cache_entry = self.relationship_cache[other_character]
            # Cache for 5 minutes
            if time.time() - cache_entry["cached_at"] < 300:
                self.cache_hits += 1
                return cache_entry["data"]
        
        # Get from database
        try:
            async with db_service.get_connection() as conn:
                relationship_data = await conn.fetchrow("""
                    SELECT * FROM character_relationships 
                    WHERE character_a = $1 AND character_b = $2
                """, self.character_id, other_character)
                
                if relationship_data:
                    result = dict(relationship_data)
                else:
                    # No relationship data yet
                    result = {
                        "character_a": self.character_id,
                        "character_b": other_character,
                        "relationship_strength": 0.0,
                        "interaction_count": 0,
                        "relationship_type": "neutral"
                    }
                
                # Cache the result
                self.relationship_cache[other_character] = {
                    "data": result,
                    "cached_at": time.time()
                }
                
                self.cache_misses += 1
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get relationship patterns: {e}")
            return {}
    
    async def get_character_evolution_data(self) -> Dict:
        """Get character evolution data"""
        try:
            char_data = await db_service.get_character(self.character_id)
            return char_data if char_data else {}
        except Exception as e:
            logger.error(f"❌ Failed to get character evolution data: {e}")
            return {}
    
    async def update_personality_traits(self, trait_changes: Dict[str, float]) -> bool:
        """Update personality traits in database"""
        try:
            return await db_service.update_character_personality(
                character_id=self.character_id,
                personality_changes=trait_changes
            )
        except Exception as e:
            logger.error(f"❌ Failed to update personality traits: {e}")
            return False
    
    async def get_memory_stats(self) -> Dict:
        """Get comprehensive memory statistics"""
        try:
            # Get database stats
            dashboard_data = await db_service.get_character_performance_dashboard(self.character_id)
            
            # Add cache performance
            cache_stats = {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
                "cached_conversations": len(self.recent_conversations),
                "cached_relationships": len(self.relationship_cache)
            }
            
            return {
                **dashboard_data,
                "cache_performance": cache_stats,
                "memory_system": "enhanced_hybrid"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    # HELPER METHODS
    
    async def _load_recent_memories(self):
        """Load recent memories into cache"""
        try:
            # Load recent conversations
            async with db_service.get_connection() as conn:
                recent_speeches = await conn.fetch("""
                    SELECT id, timestamp FROM session_speeches 
                    WHERE character_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT $2
                """, self.character_id, settings.MEMORY_CACHE_SIZE)
                
                for speech in recent_speeches:
                    memory_entry = MemoryEntry(
                        id=speech["id"],
                        character_id=self.character_id,
                        memory_type="conversation",
                        timestamp=speech["timestamp"].timestamp(),
                        importance_score=0.5,
                        qdrant_id=speech["id"],
                        db_table="session_speeches",
                        db_id=speech["id"]
                    )
                    self.recent_conversations.append(memory_entry)
            
            logger.info(f"📚 Loaded {len(self.recent_conversations)} recent memories to cache")
            
        except Exception as e:
            logger.warning(f"Could not load recent memories: {e}")
    
    def _serialize_context_for_embedding(self, context_data: Dict) -> str:
        """Convert context data to text for embedding"""
        
        text_parts = []
        
        if "event_type" in context_data:
            text_parts.append(f"Event: {context_data['event_type']}")
        
        if "topic" in context_data:
            text_parts.append(f"Topic: {context_data['topic']}")
        
        if "emotion" in context_data:
            text_parts.append(f"Emotion: {context_data['emotion']}")
        
        if "success_indicators" in context_data:
            text_parts.append(f"Success: {context_data['success_indicators']}")
        
        if "peer_reactions" in context_data:
            text_parts.append(f"Peer reactions: {context_data['peer_reactions']}")
        
        return " | ".join(text_parts) if text_parts else "Learning event"