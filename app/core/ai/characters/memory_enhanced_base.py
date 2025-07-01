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
from .adaptive_traits import AdaptiveTraits, SessionFeedback
from app.core.ai.memory import CharacterMemoryManager

logger = logging.getLogger(__name__)

class MemoryEnhancedBaseCharacter(BaseCharacter):
    """Base character class with memory capabilities and adaptive learning"""
    
    def __init__(self, character_id: str):
        super().__init__(character_id)
        self.memory_manager = CharacterMemoryManager(character_id)
        self.adaptive_traits = AdaptiveTraits()  # 🆕 NEW: Adaptive learning
        self._memory_initialized = False
        
        # Track current session for feedback
        self._current_session_id = None
        self._session_start_time = None
    
    async def initialize_memory(self):
        """Initialize memory system for this character"""
        if not self._memory_initialized:
            await self.memory_manager.initialize()
            self._memory_initialized = True
            logger.info(f"🧠 Memory + Adaptive traits initialized for {self.character_id}")
    
    def start_session(self, session_id: str):
        """Start tracking a new session for adaptive learning"""
        self._current_session_id = session_id
        self._session_start_time = time.time()
        logger.info(f"📝 Started tracking session {session_id} for {self.character_id}")
    
    async def generate_response(self, topic: str, context: Dict = None) -> Dict:
        """Enhanced response generation with memory and adaptive learning"""
        
        # Ensure memory is initialized
        await self.initialize_memory()
        
        # Get enhanced context from memory
        enhanced_context = await self._build_memory_context(topic, context)
        
        # 🆕 NEW: Add adaptive context
        adaptive_context = self._build_adaptive_context(topic, enhanced_context)
        enhanced_context.update(adaptive_context)
        
        # Generate response with memory + adaptive influence
        response = await self._generate_adaptive_response(topic, enhanced_context)
        
        # Store this conversation in memory
        await self._store_conversation_memory(response, topic, enhanced_context)
        
        return response
    
    def _build_adaptive_context(self, topic: str, context: Dict) -> Dict:
        """Build context based on adaptive learning"""
        
        adaptive_context = {
            "topic_preference_score": self.adaptive_traits.get_topic_preference_score(topic),
            "preferred_emotion": self.adaptive_traits.get_preferred_emotion(),
            "optimal_length": self.adaptive_traits.optimal_response_length,
            "successful_topics": list(self.adaptive_traits.successful_topics.keys())[:3],
            "adaptation_summary": self.adaptive_traits.get_adaptation_summary()
        }
        
        logger.debug(f"🎯 Adaptive context for {self.character_id}: {adaptive_context}")
        return {"adaptive": adaptive_context}
    
    async def _generate_adaptive_response(self, topic: str, context: Dict) -> Dict:
        """Generate response influenced by memory AND adaptive learning"""
        
        # Base response generation
        base_response = await super().generate_response(topic, context)
        
        # Memory influence (existing)
        memory_influence = self._apply_memory_influence(base_response, context)
        
        # 🆕 NEW: Adaptive influence
        adaptive_influence = self._apply_adaptive_influence(base_response, context)
        
        # Combine influences
        final_response = self._combine_influences(base_response, memory_influence, adaptive_influence)
        
        # Add adaptive metadata
        final_response["adaptive_metadata"] = {
            "topic_preference": context.get("adaptive", {}).get("topic_preference_score", 0.0),
            "preferred_emotion_used": context.get("adaptive", {}).get("preferred_emotion"),
            "length_optimization": abs(len(final_response["text"]) - context.get("adaptive", {}).get("optimal_length", 100))
        }
        
        return final_response
    
    def _apply_adaptive_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply adaptive learning influence to response"""
        
        try:
            adaptive_ctx = context.get("adaptive", {})
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # 1. Topic preference influence
            topic_preference = adaptive_ctx.get("topic_preference_score", 0.0)
            
            if topic_preference > 0.3:  # Successful topic
                # Be more confident and elaborate
                confidence_boosters = [
                    "I've found that",
                    "In my experience with this topic,",
                    "This is particularly interesting because"
                ]
                if random.random() < 0.4:  # 40% chance
                    influenced_text = f"{random.choice(confidence_boosters)} {influenced_text.lower()}"
                    influenced_emotion = "confident"
                    
            elif topic_preference < -0.3:  # Failed topic
                # Be more cautious
                caution_phrases = [
                    "I'm still exploring this, but",
                    "This is complex, however",
                    "I need to think more about this, but"
                ]
                if random.random() < 0.3:  # 30% chance
                    influenced_text = f"{random.choice(caution_phrases)} {influenced_text.lower()}"
                    influenced_emotion = "thinking"
            
            # 2. Preferred emotion influence
            preferred_emotion = adaptive_ctx.get("preferred_emotion")
            if preferred_emotion and random.random() < 0.5:  # 50% chance to use preferred
                influenced_emotion = preferred_emotion
            
            # 3. Length optimization
            optimal_length = adaptive_ctx.get("optimal_length", 100)
            current_length = len(influenced_text)
            
            if current_length < optimal_length * 0.7:  # Too short
                # Add elaboration
                elaboration_phrases = [
                    "Let me expand on this -",
                    "To elaborate further,",
                    "What's particularly noteworthy is that"
                ]
                influenced_text = f"{influenced_text} {random.choice(elaboration_phrases)} this opens up many fascinating possibilities."
                
            elif current_length > optimal_length * 1.3:  # Too long
                # Truncate intelligently (keep first sentence + conclusion)
                sentences = influenced_text.split('. ')
                if len(sentences) > 2:
                    influenced_text = f"{sentences[0]}. {sentences[-1]}"
            
            # 4. Successful topic reinforcement
            successful_topics = adaptive_ctx.get("successful_topics", [])
            current_topic = context.get("topic", "")
            
            if any(topic in current_topic for topic in successful_topics):
                # Reference past success subtly
                success_references = [
                    "Building on what we've discussed before,",
                    "As I've been thinking about,",
                    "This connects to something important -"
                ]
                if random.random() < 0.25:  # 25% chance
                    influenced_text = f"{random.choice(success_references)} {influenced_text}"
            
            logger.debug(f"🎯 Applied adaptive influence to {self.character_id}")
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to apply adaptive influence: {e}")
            return None
    
    def _combine_influences(self, base_response: Dict, memory_influence: Optional[Dict], adaptive_influence: Optional[Dict]) -> Dict:
        """Combine base response with memory and adaptive influences"""
        
        final_response = base_response.copy()
        
        # Apply memory influence first (if exists)
        if memory_influence:
            final_response["text"] = memory_influence.get("text", final_response["text"])
            final_response["facialExpression"] = memory_influence.get("emotion", final_response["facialExpression"])
        
        # Then apply adaptive influence (if exists)
        if adaptive_influence:
            final_response["text"] = adaptive_influence.get("text", final_response["text"])
            final_response["facialExpression"] = adaptive_influence.get("emotion", final_response["facialExpression"])
        
        return final_response
    
    async def end_session_with_feedback(self, session_id: str, other_participants: List[str], topic: str, response_text: str, quality_score: float = 0.5):
        """End session and provide feedback for adaptive learning"""
        
        if session_id != self._current_session_id:
            logger.warning(f"Session ID mismatch: {session_id} vs {self._current_session_id}")
            return
        
        session_duration = time.time() - (self._session_start_time or time.time())
        
        # Create feedback
        feedback = SessionFeedback(
            session_id=session_id,
            topic=topic,
            response_text=response_text,
            duration=session_duration,
            timestamp=time.time(),
            other_participants=other_participants,
            response_quality_score=quality_score,
            conversation_continued=len(other_participants) > 0,  # Simple heuristic
            topic_shift_caused=False  # Will be enhanced later
        )
        
        # Add to adaptive traits
        self.adaptive_traits.add_session_feedback(feedback)
        
        logger.info(f"✅ Session {session_id} feedback processed for {self.character_id}")
        logger.info(f"📊 New adaptation summary: {self.adaptive_traits.get_adaptation_summary()}")
        
        # Reset session tracking
        self._current_session_id = None
        self._session_start_time = None
    
    async def get_adaptive_summary(self) -> Dict:
        """Get comprehensive adaptive learning summary"""
        
        base_summary = await self.get_memory_summary()
        adaptive_summary = self.adaptive_traits.get_adaptation_summary()
        
        return {
            **base_summary,
            "adaptive_learning": adaptive_summary,
            "character_evolution": {
                "sessions_completed": len(self.adaptive_traits.recent_feedback),
                "most_successful_topic": max(self.adaptive_traits.successful_topics.items(), 
                                           key=lambda x: x[1], default=("none", 0))[0],
                "learning_speed": self.adaptive_traits.adaptation_rate,
                "evolution_stage": self._determine_evolution_stage()
            }
        }
    
    def _determine_evolution_stage(self) -> str:
        """Determine current evolution stage based on learning"""
        
        sessions_count = len(self.adaptive_traits.recent_feedback)
        
        if sessions_count < 5:
            return "initial_learning"
        elif sessions_count < 15:
            return "pattern_recognition"
        elif sessions_count < 30:
            return "personality_formation"
        else:
            return "mature_adaptation"
    
    # Keep all existing methods from the original file...
    async def _build_memory_context(self, topic: str, context: Dict = None) -> Dict:
        """Build enhanced context using memory (existing method)"""
        # [Keep original implementation]
        enhanced_context = context.copy() if context else {}
        
        try:
            similar_memories = await self.memory_manager.recall_similar_conversations(
                current_topic=topic,
                limit=3
            )
            
            other_participants = enhanced_context.get("other_participants", [])
            relationship_patterns = {}
            
            for participant in other_participants:
                relationship_patterns[participant] = await self.memory_manager.get_relationship_pattern(participant)
            
            recent_conversations = self.memory_manager.get_recent_conversations(limit=3)
            topic_expertise = self.memory_manager.get_topic_expertise(topic)
            
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