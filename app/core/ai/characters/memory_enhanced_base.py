# app/core/ai/characters/memory_enhanced_base.py
"""
Memory-enhanced BaseCharacter that integrates with the A2AIs memory system
"""

import asyncio
import logging
import time
import random
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass

from .base import BaseCharacter, PersonalityTraits, EmotionalState
from app.core.ai.memory import CharacterMemoryManager

logger = logging.getLogger(__name__)

class MemoryEnhancedBaseCharacter(BaseCharacter):
    """Base character class with memory capabilities"""
    
    def __init__(self, character_id: str):
        super().__init__(character_id)
        self.memory_manager = CharacterMemoryManager(character_id)
        self._memory_initialized = False
    
    async def initialize_memory(self):
        """Initialize memory system for this character"""
        if not self._memory_initialized:
            await self.memory_manager.initialize()
            self._memory_initialized = True
            logger.info(f"🧠 Memory initialized for {self.character_id}")
    
    async def generate_response(self, topic: str, context: Dict = None) -> Dict:
        """Enhanced response generation with memory integration"""
        
        # Ensure memory is initialized
        await self.initialize_memory()
        
        # Get enhanced context from memory
        enhanced_context = await self._build_memory_context(topic, context)
        
        # Generate response with memory influence
        response = await self._generate_memory_influenced_response(topic, enhanced_context)
        
        # Store this conversation in memory
        await self._store_conversation_memory(response, topic, enhanced_context)
        
        return response
    
    async def _build_memory_context(self, topic: str, context: Dict = None) -> Dict:
        """Build enhanced context using memory"""
        
        enhanced_context = context.copy() if context else {}
        
        try:
            # 1. Recall similar conversations
            similar_memories = await self.memory_manager.recall_similar_conversations(
                current_topic=topic,
                limit=3
            )
            
            # 2. Get relationship patterns with other participants
            other_participants = enhanced_context.get("other_participants", [])
            relationship_patterns = {}
            
            for participant in other_participants:
                relationship_patterns[participant] = await self.memory_manager.get_relationship_pattern(participant)
            
            # 3. Get recent conversations for context
            recent_conversations = self.memory_manager.get_recent_conversations(limit=3)
            
            # 4. Get topic expertise
            topic_expertise = self.memory_manager.get_topic_expertise(topic)
            
            # Add memory data to context
            enhanced_context.update({
                "similar_memories": similar_memories,
                "relationship_patterns": relationship_patterns,
                "recent_conversations": recent_conversations,
                "topic_expertise": topic_expertise,
                "memory_stats": await self.memory_manager.get_memory_stats()
            })
            
            logger.debug(f"🧠 Built memory context: {len(similar_memories)} memories, {len(relationship_patterns)} relationships")
            
        except Exception as e:
            logger.error(f"❌ Failed to build memory context: {e}")
            # Continue without memory context
        
        return enhanced_context
    
    async def _generate_memory_influenced_response(self, topic: str, context: Dict) -> Dict:
        """Generate response influenced by memory"""
        
        # Base response generation
        base_response = await super().generate_response(topic, context)
        
        # Memory influence on response
        memory_influence = self._apply_memory_influence(base_response, context)
        
        # Update response with memory influence
        if memory_influence:
            base_response["text"] = memory_influence.get("text", base_response["text"])
            base_response["facialExpression"] = memory_influence.get("emotion", base_response["facialExpression"])
            
            # Add memory metadata
            base_response["memory_influence"] = {
                "similar_memory_count": len(context.get("similar_memories", [])),
                "topic_expertise": context.get("topic_expertise", 0.0),
                "relationship_context": len(context.get("relationship_patterns", {}))
            }
        
        return base_response
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply memory-based influence to response"""
        
        try:
            similar_memories = context.get("similar_memories", [])
            relationship_patterns = context.get("relationship_patterns", {})
            topic_expertise = context.get("topic_expertise", 0.0)
            
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # 1. Reference similar conversations (if any)
            if similar_memories and random.random() < 0.3:  # 30% chance to reference past
                memory = similar_memories[0]["memory"]
                memory_text = memory.get("text", "")[:50]
                
                memory_references = [
                    f"As I mentioned before, {memory_text}...",
                    f"This reminds me of when we discussed {memory.get('topic', 'this')}...",
                    f"I've been thinking about this since our last conversation about {memory.get('topic', 'this')}..."
                ]
                
                influenced_text = f"{random.choice(memory_references)} {influenced_text}"
            
            # 2. Relationship-based modifications
            for participant, pattern in relationship_patterns.items():
                relationship_type = pattern.get("relationship_type", "neutral")
                interaction_count = pattern.get("interaction_count", 0)
                
                if interaction_count > 5:  # Established relationship
                    if relationship_type == "collaborative":
                        if random.random() < 0.2:  # 20% chance
                            influenced_text = f"I appreciate {participant}'s perspective on this. {influenced_text}"
                    elif relationship_type == "competitive":
                        if random.random() < 0.2:
                            influenced_text = f"While {participant} might disagree, {influenced_text}"
            
            # 3. Topic expertise influence
            if topic_expertise > 0.5:  # High expertise
                expertise_phrases = [
                    "In my experience with this topic,",
                    "Having discussed this extensively,",
                    "Based on my understanding of this subject,"
                ]
                if random.random() < 0.25:  # 25% chance
                    influenced_text = f"{random.choice(expertise_phrases)} {influenced_text}"
                    influenced_emotion = "confident"  # More confident with expertise
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to apply memory influence: {e}")
            return None
    
    async def _store_conversation_memory(self, response: Dict, topic: str, context: Dict):
        """Store the conversation in memory"""
        
        try:
            other_participants = context.get("other_participants", [])
            
            await self.memory_manager.store_conversation(
                text=response["text"],
                emotion=response["facialExpression"],
                topic=topic,
                other_participants=other_participants
            )
            
            logger.debug(f"🧠 Stored conversation memory for {self.character_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation memory: {e}")
    
    async def get_memory_summary(self) -> Dict:
        """Get comprehensive memory summary for this character"""
        
        await self.initialize_memory()
        
        return await self.memory_manager.get_memory_stats()
    
    async def recall_topic_history(self, topic: str) -> List[Dict]:
        """Recall conversation history for a specific topic"""
        
        await self.initialize_memory()
        
        return await self.memory_manager.recall_similar_conversations(topic)
    
    async def get_relationship_summary(self) -> Dict:
        """Get relationship summary with all other characters"""
        
        await self.initialize_memory()
        
        relationships = {}
        known_characters = ["claude", "gpt", "grok"]
        
        for character in known_characters:
            if character != self.character_id:
                relationships[character] = await self.memory_manager.get_relationship_pattern(character)
        
        return relationships