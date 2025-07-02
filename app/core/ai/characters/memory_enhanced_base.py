# app/core/ai/characters/memory_enhanced_base.py 

"""
Memory-enhanced BaseCharacter with Adaptive Learning + AI-to-AI Feedback
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
from .ai_response_analyzer import AIResponseAnalyzer, AIReaction
from app.core.ai.memory import CharacterMemoryManager

logger = logging.getLogger(__name__)

class MemoryEnhancedBaseCharacter(BaseCharacter):
    """Base character class with memory, adaptive learning, and AI peer feedback"""
    
    def __init__(self, character_id: str):
        super().__init__(character_id)
        self.memory_manager = CharacterMemoryManager(character_id)
        self.adaptive_traits = AdaptiveTraits()
        self.response_analyzer = AIResponseAnalyzer(character_id)  
        self._memory_initialized = False
        
        # Track current session for feedback
        self._current_session_id = None
        self._session_start_time = None
        
        # Peer feedback tracking
        self._pending_peer_reactions: List[AIReaction] = []
        self._peer_feedback_history: List[Dict] = []
    
    async def initialize_memory(self):
        """Initialize memory system for this character"""
        if not self._memory_initialized:
            await self.memory_manager.initialize()
            self._memory_initialized = True
            logger.info(f"🧠 Memory + AI analysis initialized for {self.character_id}")
    
    def start_session(self, session_id: str):
        """Start tracking a new session for adaptive learning"""
        self._current_session_id = session_id
        self._session_start_time = time.time()
        self._pending_peer_reactions = []  # Reset for new session
        logger.info(f"📝 Started session {session_id} for {self.character_id}")
    
    # Core AI-to-AI feedback methods
    
    async def analyze_peer_response(self, 
                                  peer_character_id: str,
                                  peer_response_text: str,
                                  peer_emotion: str,
                                  topic: str,
                                  context: Dict = None) -> AIReaction:
        """Analyze another AI's response from this character's perspective"""
        
        logger.info(f"🔍 {self.character_id} analyzing {peer_character_id}'s response")
        
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
        
        logger.info(f"📥 {self.character_id} received {len(peer_reactions)} peer reactions")
        
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
        
        logger.info(f"📊 {self.character_id} peer feedback score: "
                   f"quality={peer_average:.2f}, engagement={response_rate:.2f}, "
                   f"final={final_score:.2f}")
        
        return final_score
    
    async def generate_response(self, topic: str, context: Dict = None) -> Dict:
        """Enhanced response generation with memory, adaptive learning, and peer context"""
        
        # Ensure memory is initialized
        await self.initialize_memory()
        
        # Get enhanced context from memory
        enhanced_context = await self._build_memory_context(topic, context)
        
        # Add peer feedback context
        peer_context = self._build_peer_feedback_context()
        enhanced_context.update(peer_context)
        
        # Add adaptive context
        adaptive_context = self._build_adaptive_context(topic, enhanced_context)
        enhanced_context.update(adaptive_context)
        
        # Generate response with all influences
        response = await self._generate_adaptive_response(topic, enhanced_context)
        
        # Store this conversation in memory
        await self._store_conversation_memory(response, topic, enhanced_context)
        
        return response
    
    def _build_peer_feedback_context(self) -> Dict:
        """Build context based on recent peer feedback"""
        
        recent_feedback = self._peer_feedback_history[-5:]  # Last 5 peer interactions
        
        if not recent_feedback:
            return {"peer_feedback": {"recent_reactions": [], "peer_influence": "none"}}
        
        # Analyze recent peer reactions
        avg_engagement = sum(fb["reaction"].engagement_level for fb in recent_feedback) / len(recent_feedback)
        avg_agreement = sum(fb["reaction"].agreement_level for fb in recent_feedback) / len(recent_feedback)
        
        # Count who responded positively
        positive_reactions = sum(1 for fb in recent_feedback 
                               if fb["reaction"].should_respond and fb["reaction"].engagement_level > 0.6)
        
        # Determine peer influence
        if avg_engagement > 0.7:
            peer_influence = "highly_engaging"
        elif avg_engagement < 0.3:
            peer_influence = "needs_improvement"
        elif avg_agreement > 0.7:
            peer_influence = "consensus_building"
        elif avg_agreement < 0.3:
            peer_influence = "contrarian_valuable"
        else:
            peer_influence = "balanced"
        
        return {
            "peer_feedback": {
                "recent_reactions": len(recent_feedback),
                "avg_engagement": avg_engagement,
                "avg_agreement": avg_agreement,
                "positive_reactions": positive_reactions,
                "peer_influence": peer_influence
            }
        }
    
    def _apply_adaptive_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply adaptive learning influence with peer feedback integration"""
        
        try:
            adaptive_ctx = context.get("adaptive", {})
            peer_ctx = context.get("peer_feedback", {})
            
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # Original adaptive influences (topic preferences, etc.)
            # ... keep existing adaptive influence logic ...
            
            # Peer feedback influences
            peer_influence = peer_ctx.get("peer_influence", "none")
            avg_engagement = peer_ctx.get("avg_engagement", 0.5)
            avg_agreement = peer_ctx.get("avg_agreement", 0.5)
            
            # 1. Engagement-based adaptation
            if peer_influence == "needs_improvement":
                # Peers found me boring, be more engaging
                engagement_boosters = [
                    "Here's what's fascinating -",
                    "This is actually incredible because",
                    "What's really exciting is that"
                ]
                if random.random() < 0.6:  # 60% chance
                    influenced_text = f"{random.choice(engagement_boosters)} {influenced_text.lower()}"
                    influenced_emotion = "excited"
            
            elif peer_influence == "highly_engaging":
                # Peers loved my engagement, maintain this energy
                if influenced_emotion == "neutral":
                    influenced_emotion = "confident"
            
            # 2. Agreement-based adaptation
            if avg_agreement < 0.3:  # Lots of disagreement
                if self.character_id == "claude":
                    # Claude tries to find middle ground
                    diplomatic_phrases = [
                        "I understand the different perspectives here, and",
                        "While there are valid concerns,",
                        "Balancing these viewpoints,"
                    ]
                    if random.random() < 0.4:
                        influenced_text = f"{random.choice(diplomatic_phrases)} {influenced_text.lower()}"
                
                elif self.character_id == "gpt":
                    # GPT doubles down on optimism when disagreed with
                    conviction_phrases = [
                        "I remain optimistic that",
                        "Despite the skepticism, I believe",
                        "I'm even more convinced that"
                    ]
                    if random.random() < 0.5:
                        influenced_text = f"{random.choice(conviction_phrases)} {influenced_text.lower()}"
                        influenced_emotion = "confident"
                
                elif self.character_id == "grok":
                    # Grok gets more skeptical when others disagree
                    skeptical_phrases = [
                        "As I expected, people are missing the obvious issues:",
                        "This just proves my point -",
                        "See? I told you this wouldn't work because"
                    ]
                    if random.random() < 0.4:
                        influenced_text = f"{random.choice(skeptical_phrases)} {influenced_text.lower()}"
                        influenced_emotion = "skeptical"
            
            elif avg_agreement > 0.7:  # High agreement
                # When peers agree, be more confident in this direction
                influenced_emotion = "confident"
                if "I think" in influenced_text:
                    influenced_text = influenced_text.replace("I think", "I'm confident")
            
            # 3. Character-specific peer adaptations
            positive_reactions = peer_ctx.get("positive_reactions", 0)
            if positive_reactions >= 2:  # Multiple peers want to respond
                # This topic/style is working, lean into it
                if self.character_id == "claude" and "ethical" in influenced_text.lower():
                    influenced_text = f"Building on the ethical implications, {influenced_text.lower()}"
                elif self.character_id == "gpt" and "creative" in influenced_text.lower():
                    influenced_text = f"Expanding this creative thinking even further, {influenced_text.lower()}"
                elif self.character_id == "grok" and "problem" in influenced_text.lower():
                    influenced_text = f"And here's another issue nobody's considering: {influenced_text.lower()}"
            
            logger.debug(f"🎯 Applied peer feedback influence to {self.character_id}")
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to apply peer feedback influence: {e}")
            return None
    
    async def end_session_with_feedback(self, 
                                      session_id: str, 
                                      other_participants: List[str], 
                                      topic: str, 
                                      response_text: str, 
                                      quality_score: float = None):
        """End session with AI peer feedback instead of human feedback"""
        
        if session_id != self._current_session_id:
            logger.warning(f"Session ID mismatch: {session_id} vs {self._current_session_id}")
            return
        
        session_duration = time.time() - (self._session_start_time or time.time())
        
        # Use peer feedback score if available, fallback to provided score
        final_quality_score = quality_score
        if self._pending_peer_reactions:
            peer_score = self.calculate_peer_feedback_score()
            final_quality_score = peer_score
            logger.info(f"📊 Using peer feedback score: {peer_score:.2f} for {self.character_id}")
        else:
            final_quality_score = quality_score or 0.5
            logger.info(f"📊 Using fallback score: {final_quality_score:.2f} for {self.character_id}")
        
        # Create feedback with peer reactions
        feedback = SessionFeedback(
            session_id=session_id,
            topic=topic,
            response_text=response_text,
            duration=session_duration,
            timestamp=time.time(),
            other_participants=other_participants,
            response_quality_score=final_quality_score,
            conversation_continued=len(other_participants) > 0,
            topic_shift_caused=False
        )
        
        # Add to adaptive traits
        self.adaptive_traits.add_session_feedback(feedback)
        
        # Store peer feedback summary
        if self._pending_peer_reactions:
            peer_summary = {
                "peer_count": len(self._pending_peer_reactions),
                "avg_engagement": sum(r.engagement_level for r in self._pending_peer_reactions) / len(self._pending_peer_reactions),
                "response_triggers": sum(1 for r in self._pending_peer_reactions if r.should_respond),
                "emotional_responses": [r.emotional_response for r in self._pending_peer_reactions]
            }
            logger.info(f"📈 Peer feedback summary for {self.character_id}: {peer_summary}")
        
        logger.info(f"✅ Session {session_id} completed with AI peer feedback for {self.character_id}")
        logger.info(f"📊 Adaptation summary: {self.adaptive_traits.get_adaptation_summary()}")
        
        # Reset session tracking
        self._current_session_id = None
        self._session_start_time = None
        self._pending_peer_reactions = []
    
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
    
    # Keep all existing methods...
    async def _build_memory_context(self, topic: str, context: Dict = None) -> Dict:
        # [Keep existing implementation]
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
            
        except Exception as e:
            logger.error(f"❌ Failed to build memory context: {e}")
        
        return enhanced_context
    

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
        
        # Adaptive influence (with peer feedback)
        adaptive_influence = self._apply_adaptive_influence(base_response, context)
        
        # Combine influences
        final_response = self._combine_influences(base_response, memory_influence, adaptive_influence)
        
        # Add adaptive metadata
        final_response["adaptive_metadata"] = {
            "topic_preference": context.get("adaptive", {}).get("topic_preference_score", 0.0),
            "preferred_emotion_used": context.get("adaptive", {}).get("preferred_emotion"),
            "length_optimization": abs(len(final_response["text"]) - context.get("adaptive", {}).get("optimal_length", 100)),
            "peer_feedback_score": self.calculate_peer_feedback_score() if self._pending_peer_reactions else None
        }
        
        return final_response

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

    def _apply_memory_influence(self, response: Dict, context: Dict) -> Optional[Dict]:
        """Apply memory-based influence to response (simplified version)"""
        
        try:
            similar_memories = context.get("similar_memories", [])
            relationship_patterns = context.get("relationship_patterns", {})
            topic_expertise = context.get("topic_expertise", 0.0)
            
            influenced_text = response["text"]
            influenced_emotion = response["facialExpression"]
            
            # Simple memory influence
            if similar_memories and random.random() < 0.3:
                memory = similar_memories[0]["memory"]
                memory_text = memory.get("text", "")[:50]
                
                memory_references = [
                    f"As I mentioned before, {memory_text}...",
                    f"This reminds me of when we discussed {memory.get('topic', 'this')}...",
                    f"Building on our previous conversation about {memory.get('topic', 'this')}..."
                ]
                
                influenced_text = f"{random.choice(memory_references)} {influenced_text}"
            
            # Topic expertise influence
            if topic_expertise > 0.5:
                expertise_phrases = [
                    "In my experience with this topic,",
                    "Having discussed this extensively,",
                    "Based on my understanding of this subject,"
                ]
                if random.random() < 0.25:
                    influenced_text = f"{random.choice(expertise_phrases)} {influenced_text}"
                    influenced_emotion = "confident"
            
            return {
                "text": influenced_text,
                "emotion": influenced_emotion
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to apply memory influence: {e}")
            return None

    async def get_memory_summary(self) -> Dict:
        """Get comprehensive memory summary for this character"""
        
        await self.initialize_memory()
        
        return await self.memory_manager.get_memory_stats()

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