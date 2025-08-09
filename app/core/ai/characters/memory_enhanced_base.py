# app/core/ai/characters/memory_enhanced_base.py
"""
Memory-enhanced BaseCharacter with Database Integration
Adaptive AI with persistence
"""

import asyncio
import logging
import time
import random
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .base import BaseCharacter, PersonalityTraits, EmotionalState
from .adaptive_traits import AdaptiveTraits, SessionFeedback
from .ai_response_analyzer import AIResponseAnalyzer, AIReaction
from app.core.ai.memory.enhanced_character_memory import EnhancedCharacterMemory
from app.core.database.service import db_service

logger = logging.getLogger(__name__)

class MemoryState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    FAILED = "failed"

class MemoryEnhancedBaseCharacter(BaseCharacter):
    """Base character class with THREAD-SAFE memory and database persistence"""
    
    def __init__(self, character_id: str):
        super().__init__(character_id)
        
        # Thread-safe memory initialization
        self._memory_state = MemoryState.UNINITIALIZED
        self._memory_lock = asyncio.Lock()
        self._initialization_task: Optional[asyncio.Task] = None
        
        # Enhanced memory system
        self.enhanced_memory = EnhancedCharacterMemory(character_id)
        
        # Keep existing adaptive traits (now with database backing)
        self.adaptive_traits = AdaptiveTraits()
        self.response_analyzer = AIResponseAnalyzer(character_id)
        
        # Track current session for feedback
        self._current_session_id = None
        self._session_start_time = None
        
        # Peer feedback tracking
        self._pending_peer_reactions: List[AIReaction] = []
        self._peer_feedback_history: List[Dict] = []
        
        # Database-backed personality (loaded on init)
        self._db_personality_loaded = False
        
        # Additional evolution tracking
        self.evolution_stage = "initial_learning"
        self.maturity_level = 1
        self.life_energy = 100.0
        
        # Performance tracking
        self._init_attempts = 0
        self._last_successful_init = None
        
    async def initialize_memory(self) -> bool:
        """Thread-safe memory initialization with singleton pattern"""
        
        # Fast path: already initialized
        if self._memory_state == MemoryState.READY:
            return True
        
        # Fail fast: previous initialization failed recently
        if self._memory_state == MemoryState.FAILED:
            # Retry after 60 seconds
            if (self._last_failed_init and 
                time.time() - self._last_failed_init < 60):
                return False
        
        # Thread-safe initialization
        async with self._memory_lock:
            # Double-check pattern
            if self._memory_state == MemoryState.READY:
                return True
            
            # Check if initialization is already in progress
            if self._memory_state == MemoryState.INITIALIZING:
                if self._initialization_task and not self._initialization_task.done():
                    try:
                        # Wait for existing initialization to complete
                        await asyncio.wait_for(self._initialization_task, timeout=10.0)
                        return self._memory_state == MemoryState.READY
                    except asyncio.TimeoutError:
                        logger.error(f"Memory initialization timeout for {self.character_id}")
                        self._memory_state = MemoryState.FAILED
                        self._last_failed_init = time.time()
                        return False
            
            # Start new initialization
            self._memory_state = MemoryState.INITIALIZING
            self._init_attempts += 1
            
            # Create initialization task
            self._initialization_task = asyncio.create_task(
                self._perform_initialization()
            )
            
            try:
                success = await asyncio.wait_for(
                    self._initialization_task, 
                    timeout=15.0
                )
                
                if success:
                    self._memory_state = MemoryState.READY
                    self._last_successful_init = time.time()
                    logger.info(f"Memory initialized for {self.character_id} (attempt {self._init_attempts})")
                    return True
                else:
                    self._memory_state = MemoryState.FAILED
                    self._last_failed_init = time.time()
                    logger.error(f"Memory initialization failed for {self.character_id}")
                    return False
                    
            except asyncio.TimeoutError:
                logger.error(f"Memory initialization timeout for {self.character_id}")
                self._memory_state = MemoryState.FAILED
                self._last_failed_init = time.time()
                if self._initialization_task:
                    self._initialization_task.cancel()
                return False
            
            except Exception as e:
                logger.error(f"Memory initialization error for {self.character_id}: {e}")
                self._memory_state = MemoryState.FAILED
                self._last_failed_init = time.time()
                return False
            
    async def _perform_initialization(self) -> bool:
        """Actual initialization logic (called from locked context)"""
        try:
            # Initialize enhanced memory
            await self.enhanced_memory.initialize()
            
            # Load personality from database
            await self._load_personality_from_database()
            
            logger.debug(f"🧠 Enhanced memory + database persistence initialized for {self.character_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to perform memory initialization: {e}")
            return False
    
    async def _load_personality_from_database(self):
        """Load personality traits from database with error handling"""
        try:
            char_data = await self.enhanced_memory.get_character_evolution_data()
            
            if char_data:
                # Update personality traits from database
                self.personality.analytical = char_data.get("analytical_score", 0.5)
                self.personality.creative = char_data.get("creative_score", 0.5)
                self.personality.assertive = char_data.get("assertive_score", 0.5)
                self.personality.empathetic = char_data.get("empathetic_score", 0.5)
                self.personality.skeptical = char_data.get("skeptical_score", 0.5)
                
                # Load evolution data
                self.evolution_stage = char_data.get("evolution_stage", "initial_learning")
                self.maturity_level = char_data.get("maturity_level", 1)
                self.life_energy = char_data.get("life_energy", 100.0)
                
                self._db_personality_loaded = True
                
                logger.debug(f"Loaded personality from database: {self.character_id}")
                logger.debug(f"   Stage: {self.evolution_stage}, Energy: {self.life_energy}")
            else:
                logger.info(f"ℹNo existing personality data for {self.character_id}, using defaults")
                
        except Exception as e:
            logger.warning(f"Could not load personality from database for {self.character_id}: {e}")
    
    def start_session(self, session_id: str):
        """Start tracking a new session for adaptive learning"""
        self._current_session_id = session_id
        self._session_start_time = time.time()
        self._pending_peer_reactions = []  # Reset for new session
        logger.info(f"Started session {session_id} for {self.character_id}")
    
    # Core AI-to-AI feedback methods
    async def analyze_peer_response(self, 
                                  peer_character_id: str,
                                  peer_response_text: str,
                                  peer_emotion: str,
                                  topic: str,
                                  context: Dict = None) -> AIReaction:
        """Analyze another AI's response from this character's perspective"""
        
        logger.info(f"{self.character_id} analyzing {peer_character_id}'s response")
        
        reaction = await self.response_analyzer.analyze_response(
            other_character_id=peer_character_id,
            response_text=peer_response_text,
            response_emotion=peer_emotion,
            topic=topic,
            context=context or {}
        )
        
        # Store reaction for potential use
        self._peer_feedback_history.append({
            "timestamp": time.time(),
            "peer_character": peer_character_id,
            "reaction": reaction,
            "topic": topic
        })
        
        logger.info(f"📊 {self.character_id} reaction to {peer_character_id}: "
                   f"engagement={reaction.engagement_level:.2f}, "
                   f"should_respond={reaction.should_respond}")
        
        return reaction
    
    async def receive_peer_feedback(self, peer_reactions: List[AIReaction]):
        """Receive feedback from other AI characters"""
        
        self._pending_peer_reactions.extend(peer_reactions)
        
        logger.info(f"{self.character_id} received {len(peer_reactions)} peer reactions")
        
        # Log peer feedback summary
        for reaction in peer_reactions:
            logger.info(f"   {reaction.analyzer_character}: "
                       f"quality={reaction.get_overall_quality_score():.2f}, "
                       f"engagement={reaction.engagement_level:.2f}, "
                       f"should_respond={reaction.should_respond}")
    
    def calculate_peer_feedback_score(self) -> float:
        """Calculate quality score based on peer AI reactions"""
        
        if not self._pending_peer_reactions:
            return 0.5  # Neutral if no peer feedback
        
        # Average the overall quality scores from peers
        total_score = sum(reaction.get_overall_quality_score() 
                         for reaction in self._pending_peer_reactions)
        
        peer_average = total_score / len(self._pending_peer_reactions)
        
        # Weight by number of peers who want to respond (engagement indicator)
        response_rate = sum(1 for reaction in self._pending_peer_reactions 
                           if reaction.should_respond) / len(self._pending_peer_reactions)
        
        # Combine peer quality with response engagement
        final_score = (peer_average * 0.7) + (response_rate * 0.3)
        
        logger.info(f"{self.character_id} peer feedback score: "
                   f"quality={peer_average:.2f}, engagement={response_rate:.2f}, "
                   f"final={final_score:.2f}")
        
        return final_score
    
    async def generate_response(self, topic: str, context: Dict = None) -> Dict:
        """Enhanced response generation with memory initialization"""
        
        # Try to initialize memory, but don't block if it fails
        memory_ready = await self.initialize_memory()
        
        if not memory_ready:
            logger.warning(f"⚠️ Memory not ready for {self.character_id}, using fallback mode")
            # Continue with basic functionality
            context = context or {}
            context["memory_available"] = False
        else:
            context = context or {}
            context["memory_available"] = True
        
        # Build enhanced context (with fallback if memory not ready)
        if memory_ready:
            enhanced_context = await self._build_enhanced_context(topic, context)
        else:
            enhanced_context = await self._build_fallback_context(topic, context)
        
        # Generate response with all influences
        response = await self._generate_database_backed_response(topic, enhanced_context)
        
        # Store conversation in memory (only if memory is ready)
        if memory_ready:
            try:
                await self._store_conversation_with_persistence(response, topic, enhanced_context)
            except Exception as e:
                logger.warning(f"Failed to store conversation in memory: {e}")
        
        return response
    
    async def _build_fallback_context(self, topic: str, context: Dict) -> Dict:
        """Build basic context when memory is not available"""
        
        fallback_context = context.copy() if context else {}
        
        # Add minimal context
        fallback_context.update({
            "similar_memories": [],
            "relationship_patterns": {},
            "evolution_data": {
                "evolution_stage": self.evolution_stage,
                "maturity_level": self.maturity_level,
                "life_energy": self.life_energy
            },
            "learning_history": [],
            "memory_stats": {"status": "fallback_mode"},
            "adaptive": {
                "successful_topics": [],
                "failed_topics": [],
                "preferred_emotion": "neutral",
                "optimal_response_length": 100.0,
                "sessions_learned_from": 0,
                "topic_preference_score": 0.0
            },
            "peer_feedback": {
                "avg_engagement": 0.5,
                "avg_agreement": 0.5,
                "peer_count": 0
            }
        })
        
        logger.debug(f"Built fallback context for {self.character_id}")
        return fallback_context
    
    async def _build_enhanced_context(self, topic: str, context: Dict = None) -> Dict:
        """Build enhanced context using database + memory"""
        
        enhanced_context = context.copy() if context else {}
        
        try:
            session_id = enhanced_context.get("session_id")
            if session_id:
                # Get last 5 conversations
                recent_conversation = await self._get_recent_conversation_context(session_id)
                enhanced_context["recent_conversation"] = recent_conversation
                
                # If peer-triggered, mark who triggered it
                if enhanced_context.get("peer_triggered"):
                    trigger_reaction = enhanced_context.get("trigger_reaction")
                    if trigger_reaction:
                        enhanced_context["responding_to_character"] = trigger_reaction.target_character
                        enhanced_context["peer_reaction_details"] = {
                            "engagement": trigger_reaction.engagement_level,
                            "agreement": trigger_reaction.agreement_level,
                            "specific_reaction": getattr(trigger_reaction, 'specific_reaction', '')
                        }
            # 1. Similar conversations from hybrid memory
            similar_memories = await self.enhanced_memory.find_similar_conversations(
                current_text=topic,
                limit=3
            )
            
            # 2. Relationship patterns from database
            other_participants = enhanced_context.get("other_participants", [])
            relationship_patterns = {}
            
            for participant in other_participants:
                relationship_patterns[participant] = await self.enhanced_memory.get_relationship_patterns(participant)
            
            # 3. Character evolution data from database
            evolution_data = await self.enhanced_memory.get_character_evolution_data()
            
            # 4. Learning history from database
            learning_history = await db_service.get_character_learning_history(
                character_id=self.character_id,
                limit=5,
                event_types=["breakthrough", "success", "failure"]
            )
            
            # ADAPTIVE TRAITS DATA
            adaptive_summary = self.adaptive_traits.get_adaptation_summary()
            adaptive_context = {
                "successful_topics": list(self.adaptive_traits.successful_topics.keys()),
                "failed_topics": list(self.adaptive_traits.failed_topics.keys()),
                "preferred_emotion": self.adaptive_traits.get_preferred_emotion(),
                "optimal_response_length": self.adaptive_traits.optimal_response_length,
                "sessions_learned_from": len(self.adaptive_traits.recent_feedback),
                "topic_preference_score": self.adaptive_traits.get_topic_preference_score(topic),
                "adaptation_summary": adaptive_summary
            }
            
            #PEER FEEDBACK DATA
            peer_feedback_context = {}
            if self._pending_peer_reactions:
                peer_engagement_scores = [r.engagement_level for r in self._pending_peer_reactions]
                peer_agreement_scores = [r.agreement_level for r in self._pending_peer_reactions]
                
                peer_feedback_context = {
                    "avg_engagement": sum(peer_engagement_scores) / len(peer_engagement_scores),
                    "avg_agreement": sum(peer_agreement_scores) / len(peer_agreement_scores),
                    "peer_count": len(self._pending_peer_reactions),
                    "should_respond_count": sum(1 for r in self._pending_peer_reactions if r.should_respond),
                    "recent_reactions": [
                        {
                            "analyzer": r.analyzer_character,
                            "engagement": r.engagement_level,
                            "agreement": r.agreement_level,
                            "should_respond": r.should_respond,
                            "emotional_response": r.emotional_response
                        }
                        for r in self._pending_peer_reactions[-3:]  # Last 3 reactions
                    ]
                }
            else:
                # Get historical peer feedback summary
                peer_feedback_context = await self._get_historical_peer_feedback_summary()
            
            enhanced_context.update({
                "similar_memories": similar_memories,
                "relationship_patterns": relationship_patterns,
                "evolution_data": evolution_data,
                "learning_history": learning_history,
                "memory_stats": await self.enhanced_memory.get_memory_stats(),
                "adaptive": adaptive_context,
                "peer_feedback": peer_feedback_context
            })
            
            logger.debug(f"   Enhanced context built for {self.character_id}")
            logger.debug(f"   Similar memories: {len(similar_memories)}")
            logger.debug(f"   Relationship patterns: {len(relationship_patterns)}")
            logger.debug(f"   Adaptive sessions: {adaptive_context['sessions_learned_from']}")
            logger.debug(f"   Peer reactions: {peer_feedback_context.get('peer_count', 0)}")
            
        except Exception as e:
            logger.error(f"Failed to build enhanced context: {e}")
        
        return enhanced_context
    
    async def _get_recent_conversation_context(self, session_id: str, limit: int = 5) -> str:
        """Get recent conversation context for natural flow"""
        
        try:
            # Get recent speeches from database
            recent_speeches = []
            
            # Get from in-memory cache first (if available)
            if hasattr(self, 'recent_conversations') and self.recent_conversations:
                # In-memory cache
                recent_entries = list(self.recent_conversations)[-limit:]
                for entry in recent_entries:
                    if hasattr(entry, 'text') and hasattr(entry, 'character_id'):
                        recent_speeches.append({
                            'character_id': getattr(entry, 'character_id', self.character_id),
                            'text': entry.text[:200],  # Limit to 200 chars
                            'emotion': getattr(entry, 'emotion', 'neutral')
                        })
            
            # If not enough in-memory entries, fetch from database
            if len(recent_speeches) < 3:
                try:
                    from app.core.database.service import db_service
                    async with db_service.get_connection() as conn:
                        db_speeches = await conn.fetch("""
                            SELECT character_id, emotion, timestamp 
                            FROM session_speeches 
                            WHERE session_id = $1 
                            ORDER BY timestamp DESC 
                            LIMIT $2
                        """, session_id, limit)
                        
                        for speech in db_speeches:
                            if speech['character_id'] != self.character_id:  # Only other characters' speeches
                                recent_speeches.append({
                                    'character_id': speech['character_id'],
                                    'text': f"[{speech['emotion']} response about the topic]",
                                    'emotion': speech['emotion']
                                })
                            
                except Exception as db_error:
                    logger.warning(f"Could not get conversation from database: {db_error}")
            
            # Format conversation context
            if not recent_speeches:
                return "This is the start of our conversation."
            
            context_lines = []
            for speech in reversed(recent_speeches[-3:]):  # Last 3, chronological order
                context_lines.append(f"{speech['character_id'].upper()}: {speech['text']} ({speech['emotion']})")
            
            conversation_context = "\n".join(context_lines)
            
            logger.debug(f"Conversation context for {self.character_id}:\n{conversation_context}")
            return conversation_context
            
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return "This is the start of our conversation."
    
    async def _get_historical_peer_feedback_summary(self) -> Dict:
        """Get historical peer feedback summary when no current reactions"""
        
        try:
            if not self._peer_feedback_history:
                return {"avg_engagement": 0.5, "avg_agreement": 0.5, "peer_count": 0}
            
            # Get last 10 peer feedback entries
            recent_feedback = self._peer_feedback_history[-10:]
            
            engagements = [fb["reaction"].engagement_level for fb in recent_feedback]
            agreements = [fb["reaction"].agreement_level for fb in recent_feedback]
            
            return {
                "avg_engagement": sum(engagements) / len(engagements) if engagements else 0.5,
                "avg_agreement": sum(agreements) / len(agreements) if agreements else 0.5,
                "peer_count": len(recent_feedback),
                "historical": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical peer feedback: {e}")
            return {"avg_engagement": 0.5, "avg_agreement": 0.5, "peer_count": 0}
        
        
    async def _generate_database_backed_response(self, topic: str, context: Dict) -> Dict:
        """Generate response with database-backed personality"""
        
        # Use database personality if loaded
        if self._db_personality_loaded:
            logger.debug(f"🎭 Using database personality for {self.character_id}")
        
        # Generate base response (using potentially evolved personality)
        base_response = await super().generate_response(topic, context)
        
        # Apply memory influence
        memory_influence = self._apply_enhanced_memory_influence(base_response, context)

        if hasattr(self, '_apply_memory_influence'):
            child_memory_influence = self._apply_memory_influence(base_response, context)
            # Combine with enhanced memory influence
            if child_memory_influence:
                memory_influence = child_memory_influence
        
        # Apply adaptive influence (now with database backing)
        adaptive_influence = self._apply_database_backed_adaptive_influence(base_response, context)
        
        # Combine influences
        final_response = self._combine_influences(base_response, memory_influence, adaptive_influence)
        
        # Add enhanced metadata
        final_response["enhanced_metadata"] = {
            "database_personality_used": self._db_personality_loaded,
            "evolution_stage": self.evolution_stage,
            "maturity_level": self.maturity_level,
            "life_energy": self.life_energy,
            "memory_system": "enhanced_hybrid"
        }
        
        return final_response
    
    async def _store_conversation_with_persistence(self, response: Dict, topic: str, context: Dict):
        """Store conversation using enhanced memory (hybrid storage) - WITH ERROR HANDLING"""
        
        try:
            session_id = context.get("session_id", self._current_session_id or "default")
            
            # Store using enhanced memory (handles Qdrant + PostgreSQL)
            memory_id = await self.enhanced_memory.store_conversation_memory(
                session_id=session_id,
                speech_text=response["text"],
                emotion=response["facialExpression"],
                duration=response.get("duration", 3.0),
                voice_config=response.get("voice_config", {}),
                context={
                    "topic": topic,
                    "other_participants": context.get("other_participants", []),
                    "triggered_by": context.get("triggered_by", "manual"),
                    "round_number": context.get("round_number"),
                    "generation_time_ms": response.get("generation_time_ms")
                }
            )
            
            if memory_id:
                logger.info(f"Stored conversation with persistence: {memory_id}")
            else:
                logger.warning(f"Failed to store conversation in memory for {self.character_id}")
            
        except Exception as e:
            logger.error(f"Failed to store conversation with persistence: {e}")
    
    def _apply_enhanced_memory_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply memory influence using enhanced system"""
        
        try:
            similar_memories = context.get("similar_memories", [])
            evolution_data = context.get("evolution_data", {})
            
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # 1. Similar memory influence
            if similar_memories:
                most_similar = similar_memories[0]
                similarity_score = most_similar.get("similarity_score", 0.0)
                
                if similarity_score > 0.8:  # Very similar past experience
                    past_emotion = most_similar.get("emotion", "neutral")
                    if past_emotion != "neutral" and influenced_emotion == "neutral":
                        influenced_emotion = past_emotion
                        logger.debug(f"Applied similar memory emotion: {past_emotion}")
            
            # 2. Evolution stage influence
            evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
            
            if evolution_stage == "mature_adaptation":
                # More sophisticated language
                if "I think" in influenced_text:
                    influenced_text = influenced_text.replace("I think", "In my experience")
                elif "maybe" in influenced_text:
                    influenced_text = influenced_text.replace("maybe", "it's likely that")
            
            elif evolution_stage == "initial_learning":
                # More tentative language
                if not any(word in influenced_text.lower() for word in ["i think", "maybe", "perhaps"]):
                    if random.random() < 0.3:
                        influenced_text = f"I think {influenced_text.lower()}"
            
            # 3. Maturity level influence
            maturity_level = evolution_data.get("maturity_level", 1)
            if maturity_level >= 5:
                # Add more nuanced expressions
                if influenced_emotion == "neutral" and random.random() < 0.2:
                    influenced_emotion = "thinking"
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"Failed to apply enhanced memory influence: {e}")
            return None
    
    def _apply_database_backed_adaptive_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply adaptive influence with database backing"""
        
        try:
            learning_history = context.get("learning_history", [])
            evolution_data = context.get("evolution_data", {})
            
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # Analyze recent learning events
            recent_successes = [event for event in learning_history if event.get("event_type") == "success"]
            recent_failures = [event for event in learning_history if event.get("event_type") == "failure"]
            
            # Success pattern adaptation
            if len(recent_successes) > len(recent_failures):
                # Character is doing well, be more confident
                if influenced_emotion == "neutral":
                    influenced_emotion = "confident"
                
                if "I'm not sure" in influenced_text:
                    influenced_text = influenced_text.replace("I'm not sure", "I believe")
            
            # Failure pattern adaptation
            elif len(recent_failures) > len(recent_successes):
                # Character struggling, be more cautious
                if not any(phrase in influenced_text for phrase in ["carefully", "cautiously", "consider"]):
                    if random.random() < 0.4:
                        influenced_text = f"Let me carefully consider this: {influenced_text.lower()}"
                
                if influenced_emotion == "confident":
                    influenced_emotion = "thinking"
            
            # Energy level influence
            life_energy = evolution_data.get("life_energy", 100.0)
            if life_energy < 30:
                # Low energy, more desperate responses
                if random.random() < 0.3:
                    influenced_text = f"This is important - {influenced_text.lower()}"
                    influenced_emotion = "concerned"
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"Failed to apply database-backed adaptive influence: {e}")
            return None
    
    async def end_session_with_database_persistence(self, 
                                                session_id: str, 
                                                other_participants: List[str], 
                                                topic: str, 
                                                response_text: str, 
                                                quality_score: float = None):
        """End session with COMPLETE learning integration (WITH MEMORY CHECK)"""
        
        # Only proceed if memory is ready
        memory_ready = await self.initialize_memory()
        if not memory_ready:
            logger.warning(f"Memory not ready for session end: {self.character_id}")
            return
        
        try:
            # Calculate final quality score (peer feedback + adaptive)
            peer_score = self.calculate_peer_feedback_score() if self._pending_peer_reactions else None
            final_score = peer_score if peer_score is not None else (quality_score or 0.5)
            
            # CREATE SESSION FEEDBACK FOR ADAPTIVE LEARNING
            session_feedback = SessionFeedback(
                session_id=session_id,
                topic=topic,
                response_text=response_text,
                duration=time.time() - (self._session_start_time or time.time()),
                timestamp=time.time(),
                other_participants=other_participants,
                conversation_continued=len(self._pending_peer_reactions) > 0,
                response_quality_score=final_score,
                topic_shift_caused=self._detect_topic_shift(response_text, topic)
            )
            
            # SESSION FEEDBACK TO ADAPTIVE TRAITS
            self.adaptive_traits.add_session_feedback(session_feedback)
            logger.info(f"Added session feedback to adaptive traits: score={final_score:.2f}")
            
            # Store learning event in database
            learning_event_id = await self.enhanced_memory.store_learning_event(
                session_id=session_id,
                event_type="session_completion",
                context_data={
                    "topic": topic,
                    "other_participants": other_participants,
                    "response_quality": final_score,
                    "peer_reactions_count": len(self._pending_peer_reactions),
                    "session_duration": session_feedback.duration,
                    "topic_preference_score": self.adaptive_traits.get_topic_preference_score(topic),
                    "conversation_continued": session_feedback.conversation_continued,
                    "topic_shift_caused": session_feedback.topic_shift_caused
                },
                success_score=final_score
            )
            
            # Update character evolution based on performance
            await self._update_character_evolution(final_score, session_id)
            
            # Update survival mechanics
            energy_delta = self._calculate_energy_change(final_score)
            await db_service.update_character_energy(
                character_id=self.character_id,
                energy_delta=energy_delta,
                event_type="session_completion",
                event_source="autonomous"
            )
            
            logger.info(f"Session ended with complete learning integration: {session_id}")
            logger.info(f"Learning event: {learning_event_id}, Energy delta: {energy_delta}")
            logger.info(f"Adaptive traits updated: {len(self.adaptive_traits.recent_feedback)} total sessions")
            
            # Reset session tracking
            self._current_session_id = None
            self._session_start_time = None
            self._pending_peer_reactions = []
            
        except Exception as e:
            logger.error(f"Failed to end session with persistence: {e}")
            import traceback
            traceback.print_exc()
    
    async def _update_character_evolution(self, performance_score: float, session_id: str):
        """Update character evolution based on performance"""
        
        try:
            # Increment session count
            await db_service.increment_character_stats(
                character_id=self.character_id,
                sessions=1,
                breakthroughs=1 if performance_score > 0.8 else 0
            )
            
            # Check for evolution stage progression
            char_data = await self.enhanced_memory.get_character_evolution_data()
            current_sessions = char_data.get("total_sessions", 0)
            current_stage = char_data.get("evolution_stage", "initial_learning")
            
            new_stage = None
            new_maturity = None
            
            if current_stage == "initial_learning" and current_sessions >= 10:
                new_stage = "pattern_recognition"
                new_maturity = 2
            elif current_stage == "pattern_recognition" and current_sessions >= 25:
                new_stage = "personality_formation"
                new_maturity = 3
            elif current_stage == "personality_formation" and current_sessions >= 50:
                new_stage = "mature_adaptation"
                new_maturity = 4
            
            if new_stage:
                await db_service.update_character_evolution_stage(
                    character_id=self.character_id,
                    new_stage=new_stage,
                    maturity_level=new_maturity
                )
                
                # Update local variables
                self.evolution_stage = new_stage
                self.maturity_level = new_maturity
                
                logger.info(f"Character evolution: {self.character_id} → {new_stage}")
            
            # Update personality traits based on performance
            if performance_score > 0.7:
                trait_adjustments = self._calculate_positive_trait_adjustments()
                if trait_adjustments:
                    await self.enhanced_memory.update_personality_traits(trait_adjustments)
            
        except Exception as e:
            logger.error(f"Failed to update character evolution: {e}")
    
    def _calculate_energy_change(self, performance_score: float) -> float:
        """Calculate energy change based on performance"""
        
        base_change = 0.0
        
        if performance_score > 0.8:
            base_change = 5.0  # Great performance
        elif performance_score > 0.6:
            base_change = 2.0  # Good performance
        elif performance_score > 0.4:
            base_change = 0.0  # Neutral
        else:
            base_change = -3.0  # Poor performance
        
        # Add randomness
        return base_change + random.uniform(-1.0, 1.0)
    
    def _calculate_positive_trait_adjustments(self) -> Dict[str, float]:
        """Calculate small personality trait adjustments for good performance"""
        
        adjustments = {}
        adjustment_size = 0.02  # Small incremental changes
        
        # Randomly adjust 1-2 traits slightly
        traits = ["analytical_score", "creative_score", "assertive_score", "empathetic_score", "skeptical_score"]
        selected_traits = random.sample(traits, random.randint(1, 2))
        
        for trait in selected_traits:
            current_value = getattr(self.personality, trait.replace("_score", ""), 0.5)
            if current_value < 0.9:  # Don't max out traits
                adjustments[trait] = adjustment_size
        
        return adjustments
    
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
    
    def _determine_evolution_stage(self) -> str:
        """Determine evolution stage based on learning"""
        return self.evolution_stage
    
    # Additional compatibility methods
    async def get_memory_summary(self) -> Dict:
        """Get comprehensive memory summary for this character"""
        await self.initialize_memory()
        return await self.enhanced_memory.get_memory_stats()

    async def get_adaptive_summary(self) -> Dict:
        """Get comprehensive adaptive learning summary"""
        
        base_summary = await self.get_memory_summary()
        adaptive_summary = self.adaptive_traits.get_adaptation_summary()
        peer_summary = await self.get_peer_feedback_summary()
        
        return {
            **base_summary,
            "adaptive_learning": adaptive_summary,
            "peer_feedback": peer_summary,
            "character_evolution": {
                "sessions_completed": len(self.adaptive_traits.recent_feedback),
                "most_successful_topic": max(self.adaptive_traits.successful_topics.items(), 
                                        key=lambda x: x[1], default=("none", 0))[0],
                "learning_speed": self.adaptive_traits.adaptation_rate,
                "evolution_stage": self.evolution_stage
            },
            "memory_state": self._memory_state.value,
            "memory_init_attempts": self._init_attempts
        }
    
    async def get_peer_feedback_summary(self) -> Dict:
        """Get summary of peer feedback patterns"""
        
        if not self._peer_feedback_history:
            return {"message": "No peer feedback history yet"}
        
        recent_feedback = self._peer_feedback_history[-10:]  # Last 10 interactions
        
        avg_engagement = sum(fb["reaction"].engagement_level for fb in recent_feedback) / len(recent_feedback)
        avg_agreement = sum(fb["reaction"].agreement_level for fb in recent_feedback) / len(recent_feedback)
        
        # Peer response rates
        peer_response_rates = {}
        for fb in recent_feedback:
            peer = fb["peer_character"]
            if peer not in peer_response_rates:
                peer_response_rates[peer] = {"total": 0, "responses": 0}
            peer_response_rates[peer]["total"] += 1
            if fb["reaction"].should_respond:
                peer_response_rates[peer]["responses"] += 1
        
        # Calculate response rates
        for peer in peer_response_rates:
            rate = peer_response_rates[peer]["responses"] / peer_response_rates[peer]["total"]
            peer_response_rates[peer]["rate"] = rate
        
        return {
            "character_id": self.character_id,
            "total_peer_interactions": len(self._peer_feedback_history),
            "recent_interactions": len(recent_feedback),
            "avg_engagement_received": round(avg_engagement, 2),
            "avg_agreement_received": round(avg_agreement, 2),
            "peer_response_rates": peer_response_rates,
            "most_responsive_peer": max(peer_response_rates.items(), 
                                       key=lambda x: x[1]["rate"], default=("none", {"rate": 0}))[0]
        }
    

    def _detect_topic_shift(self, response_text: str, current_topic: str) -> bool:
        """Detect if the response caused a topic shift"""
        
        try:
            # Simple keyword-based topic shift detection
            topic_keywords = current_topic.lower().split()
            response_words = response_text.lower().split()
            
            # Calculate topic overlap
            topic_word_count = len([word for word in response_words if word in topic_keywords])
            total_meaningful_words = len([word for word in response_words if len(word) > 3])
            
            if total_meaningful_words == 0:
                return False
            
            topic_relevance = topic_word_count / total_meaningful_words
            
            # If less than 10% topic relevance, consider it a topic shift
            shift_detected = topic_relevance < 0.1
            
            if shift_detected:
                logger.info(f"🔄 Topic shift detected: {topic_relevance:.2f} relevance")
            
            return shift_detected
            
        except Exception as e:
            logger.error(f"Topic shift detection failed: {e}")
            return False
        
    # PUBLIC PROPERTIES FOR MONITORING
    @property
    def memory_state(self) -> str:
        """Get current memory state"""
        return self._memory_state.value
    
    @property
    def memory_ready(self) -> bool:
        """Check if memory is ready"""
        return self._memory_state == MemoryState.READY
    
    @property
    def init_stats(self) -> Dict:
        """Get initialization statistics"""
        return {
            "attempts": self._init_attempts,
            "state": self._memory_state.value,
            "last_successful": self._last_successful_init,
            "last_failed": getattr(self, '_last_failed_init', None)
        }