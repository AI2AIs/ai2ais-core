# app/core/ai/memory/character_memory.py
import logging
import time
from typing import List, Dict
from dataclasses import dataclass
from collections import defaultdict, deque

from .embeddings import embedding_service
from .vector_store import vector_store
from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ConversationMemory:
    text: str
    emotion: str
    topic: str
    timestamp: float
    other_participants: List[str]
    memory_id: str
    
@dataclass
class RelationshipPattern:
    interaction_count: int = 0
    dominant_emotions: List[str] = None
    agreement_topics: List[str] = None
    disagreement_topics: List[str] = None
    last_interaction: float = 0.0
    
    def __post_init__(self):
        if self.dominant_emotions is None:
            self.dominant_emotions = []
        if self.agreement_topics is None:
            self.agreement_topics = []
        if self.disagreement_topics is None:
            self.disagreement_topics = []

class CharacterMemoryManager:
    def __init__(self, character_id: str):
        self.character_id = character_id
        
        # In-memory caches for performance
        self.recent_memories: deque = deque(maxlen=settings.MEMORY_CACHE_SIZE)
        self.relationship_patterns: Dict[str, RelationshipPattern] = {}
        self.topic_expertise: Dict[str, float] = defaultdict(float)  # Topic -> expertise score
        
        # Memory statistics
        self.total_conversations = 0
        self.memory_initialized = False
        
    async def initialize(self):
        """Initialize memory manager and load recent memories"""
        if self.memory_initialized:
            return
            
        try:
            # Load recent memories from vector store
            await self._load_recent_memories()
            
            # Initialize relationship patterns
            await self._initialize_relationship_patterns()
            
            self.memory_initialized = True
            logger.info(f"✅ Memory initialized for {self.character_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory for {self.character_id}: {e}")
            self.memory_initialized = True  # Continue without memory
    
    async def store_conversation(self, 
                               text: str,
                               emotion: str, 
                               topic: str,
                               other_participants: List[str] = None) -> bool:
        """Store a conversation memory"""
        
        if not self.memory_initialized:
            await self.initialize()
        
        try:
            timestamp = time.time()
            other_participants = other_participants or []
            
            # Create embedding and memory data
            memory_data = await embedding_service.embed_conversation(
                character_id=self.character_id,
                text=text,
                emotion=emotion,
                topic=topic,
                timestamp=timestamp,
                other_participants=other_participants
            )
            
            # Store in vector database
            success = await vector_store.store_memory(memory_data)
            
            if success:
                # Create conversation memory object
                conv_memory = ConversationMemory(
                    text=text,
                    emotion=emotion,
                    topic=topic,
                    timestamp=timestamp,
                    other_participants=other_participants,
                    memory_id=memory_data["id"]
                )
                
                # Add to recent memories cache
                self.recent_memories.append(conv_memory)
                
                # Update statistics
                self.total_conversations += 1
                
                # Update relationship patterns
                await self._update_relationship_patterns(other_participants, emotion, topic)
                
                # Update topic expertise
                self._update_topic_expertise(topic, emotion)
                
                logger.info(f"✅ Stored conversation memory for {self.character_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation for {self.character_id}: {e}")
            return False
    
    async def recall_similar_conversations(self, 
                                         current_topic: str,
                                         current_context: str = "",
                                         limit: int = None) -> List[Dict]:
        """Recall similar past conversations"""
        
        if not self.memory_initialized:
            await self.initialize()
        
        limit = limit or settings.MAX_MEMORIES_PER_QUERY
        
        try:
            # Create query text for embedding
            query_text = f"Topic: {current_topic}"
            if current_context:
                query_text += f"\nContext: {current_context}"
            
            # Generate query embedding
            query_vector = await embedding_service.embed_text(query_text)
            
            # Search similar memories
            similar_memories = await vector_store.search_memories(
                query_vector=query_vector,
                character_id=self.character_id,
                topic=current_topic,  # Optional topic filter
                limit=limit
            )
            
            logger.info(f"🧠 Recalled {len(similar_memories)} similar conversations for {self.character_id}")
            return similar_memories
            
        except Exception as e:
            logger.error(f"❌ Failed to recall memories for {self.character_id}: {e}")
            return []
    
    async def get_relationship_pattern(self, other_character: str) -> Dict:
        """Get relationship pattern with another character"""
        
        if not self.memory_initialized:
            await self.initialize()
        
        pattern = self.relationship_patterns.get(other_character, RelationshipPattern())
        
        # Calculate relationship strength
        strength = min(pattern.interaction_count / 10.0, 1.0)  # 0-1 scale
        
        # Determine relationship type
        relationship_type = self._determine_relationship_type(pattern)
        
        return {
            "character": other_character,
            "interaction_count": pattern.interaction_count,
            "relationship_strength": strength,
            "relationship_type": relationship_type,
            "dominant_emotions": pattern.dominant_emotions[-5:],  # Last 5
            "agreement_topics": pattern.agreement_topics[-3:],   # Last 3
            "disagreement_topics": pattern.disagreement_topics[-3:],
            "last_interaction_hours_ago": (time.time() - pattern.last_interaction) / 3600
        }
    
    def get_topic_expertise(self, topic: str) -> float:
        """Get expertise level for a topic (0.0 - 1.0)"""
        return min(self.topic_expertise.get(topic, 0.0), 1.0)
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Get recent conversation summaries"""
        recent = list(self.recent_memories)[-limit:]
        return [
            {
                "text": conv.text[:100] + "..." if len(conv.text) > 100 else conv.text,
                "emotion": conv.emotion,
                "topic": conv.topic,
                "timestamp": conv.timestamp,
                "participants": conv.other_participants
            }
            for conv in recent
        ]
    
    async def get_memory_stats(self) -> Dict:
        """Get comprehensive memory statistics"""
        
        if not self.memory_initialized:
            await self.initialize()
        
        # Get total memory count from vector store
        total_stored = await vector_store.get_character_memory_count(self.character_id)
        
        return {
            "character_id": self.character_id,
            "total_conversations": self.total_conversations,
            "total_stored_memories": total_stored,
            "recent_memories_cached": len(self.recent_memories),
            "known_relationships": len(self.relationship_patterns),
            "topic_expertise_areas": len(self.topic_expertise),
            "top_topics": sorted(self.topic_expertise.items(), 
                               key=lambda x: x[1], reverse=True)[:5],
            "memory_initialized": self.memory_initialized
        }
    
    # PRIVATE METHODS
    
    async def _load_recent_memories(self):
        """Load recent memories from vector store"""
        try:
            # This is a simplified version - in reality you'd want timestamp-based queries
            recent_memories = await vector_store.search_memories(
                query_vector=[0.0] * settings.EMBEDDING_DIMENSION,  # Dummy vector
                character_id=self.character_id,
                limit=20  # Load more, then filter recent
            )
            
            # Convert to ConversationMemory objects
            for memory_data in recent_memories:
                memory = memory_data["memory"]
                conv_memory = ConversationMemory(
                    text=memory.get("text", ""),
                    emotion=memory.get("emotion", "neutral"),
                    topic=memory.get("topic", ""),
                    timestamp=memory.get("timestamp", time.time()),
                    other_participants=memory.get("other_participants", []),
                    memory_id=memory_data["id"]
                )
                self.recent_memories.append(conv_memory)
            
            logger.debug(f"Loaded {len(self.recent_memories)} recent memories")
            
        except Exception as e:
            logger.warning(f"Could not load recent memories: {e}")
    
    async def _initialize_relationship_patterns(self):
        """Initialize relationship patterns from memory"""
        # For now, start with empty patterns
        # In a full implementation, you'd analyze stored memories
        self.relationship_patterns = {}
        logger.debug("Initialized empty relationship patterns")
    
    async def _update_relationship_patterns(self, 
                                          participants: List[str], 
                                          emotion: str, 
                                          topic: str):
        """Update relationship patterns based on interaction"""
        
        for participant in participants:
            if participant not in self.relationship_patterns:
                self.relationship_patterns[participant] = RelationshipPattern()
            
            pattern = self.relationship_patterns[participant]
            pattern.interaction_count += 1
            pattern.last_interaction = time.time()
            
            # Update emotion patterns
            pattern.dominant_emotions.append(emotion)
            if len(pattern.dominant_emotions) > 10:
                pattern.dominant_emotions = pattern.dominant_emotions[-10:]
            
            # Topic agreement/disagreement (simplified)
            if emotion in ["happy", "excited", "confident"]:
                if topic not in pattern.agreement_topics:
                    pattern.agreement_topics.append(topic)
            elif emotion in ["angry", "concerned", "skeptical"]:
                if topic not in pattern.disagreement_topics:
                    pattern.disagreement_topics.append(topic)
    
    def _update_topic_expertise(self, topic: str, emotion: str):
        """Update topic expertise based on conversation"""
        # Simple expertise calculation
        expertise_boost = 0.1
        
        # Boost more for confident emotions
        if emotion in ["confident", "excited", "thinking"]:
            expertise_boost = 0.2
        elif emotion in ["concerned", "angry"]:
            expertise_boost = 0.05
        
        self.topic_expertise[topic] += expertise_boost
    
    def _determine_relationship_type(self, pattern: RelationshipPattern) -> str:
        """Determine relationship type based on patterns"""
        
        if pattern.interaction_count < 3:
            return "new"
        
        # Analyze emotion patterns
        recent_emotions = pattern.dominant_emotions[-5:]
        positive_emotions = ["happy", "excited", "confident"]
        negative_emotions = ["angry", "concerned", "skeptical"]
        
        positive_count = sum(1 for e in recent_emotions if e in positive_emotions)
        negative_count = sum(1 for e in recent_emotions if e in negative_emotions)
        
        if positive_count > negative_count:
            return "collaborative"
        elif negative_count > positive_count:
            return "competitive"
        else:
            return "neutral"