# app/core/ai/characters/claude.py
from asyncio.log import logger
import random
from typing import List, Dict
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits
from .shared_adaptive_phrases import get_adaptive_phrases, get_response_templates, get_neutral_personality_traits

class ClaudeCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("claude")
    
    def get_base_personality(self) -> PersonalityTraits:
        """Completely neutral starting point - identical for ALL characters"""
        neutral_traits = get_neutral_personality_traits()
        return PersonalityTraits(
            analytical=neutral_traits["analytical"],
            creative=neutral_traits["creative"],
            assertive=neutral_traits["assertive"],
            empathetic=neutral_traits["empathetic"],
            skeptical=neutral_traits["skeptical"]
        )
    
    def get_response_patterns(self) -> List[str]:
        """Identical templates for ALL characters - guaranteed neutrality"""
        return get_response_templates()
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Dict:
        """Properly populated context data"""
        
        # Get enhanced memory influence from parent class
        base_influence = super()._apply_enhanced_memory_influence(response, context)
        if not base_influence:
            base_influence = {"text": response["text"], "emotion": response["facialExpression"]}
        
        influenced_text = base_influence["text"]
        influenced_emotion = base_influence["emotion"]
        
        # Get shared phrase pools
        phrases = get_adaptive_phrases()
        
        # ENHANCED: Database evolution context
        evolution_data = context.get("evolution_data", {})
        learning_history = context.get("learning_history", [])
        
        # Character grows more sophisticated over time
        evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
        maturity_level = evolution_data.get("maturity_level", 1)
        
        if evolution_stage in ["personality_formation", "mature_adaptation"]:
            if "I think" in influenced_text and maturity_level >= 3:
                influenced_text = influenced_text.replace("I think", "I've come to understand")
            elif "maybe" in influenced_text and maturity_level >= 4:
                influenced_text = influenced_text.replace("maybe", "it's quite possible that")
        
        # Learning history influence
        recent_breakthroughs = [event for event in learning_history if event.get("event_type") == "breakthrough"]
        if len(recent_breakthroughs) >= 2:
            if influenced_emotion == "neutral" and random.random() < 0.3:
                influenced_emotion = "confident"
        
        # ADAPTIVE LEARNING LOGIC - Now properly populated
        adaptive_ctx = context.get("adaptive", {})
        
        # Use learned preferred emotion (now persistent across sessions)
        preferred_emotion = adaptive_ctx.get("preferred_emotion", "neutral")
        if preferred_emotion != "neutral" and influenced_emotion == "neutral":
            influenced_emotion = preferred_emotion
            logger.debug(f"🎭 Applied learned preferred emotion: {preferred_emotion}")
        
        # Database-backed topic confidence
        successful_topics = adaptive_ctx.get("successful_topics", [])
        current_topic = context.get("topic", "")
        topic_preference_score = adaptive_ctx.get("topic_preference_score", 0.0)
        
        if topic_preference_score > 0.3:  # Confident about this topic
            if not any(phrase in influenced_text for phrase in phrases["confidence"]):
                confidence_phrase = phrases["confidence"][hash(influenced_text) % len(phrases["confidence"])]
                influenced_text = f"{confidence_phrase} {influenced_text.lower()}"
                logger.debug(f"🎯 Applied topic confidence boost: {topic_preference_score:.2f}")
            if influenced_emotion == "neutral":
                influenced_emotion = "confident"
        elif topic_preference_score < -0.3:  # Struggled with this topic before
            if not any(phrase in influenced_text for phrase in phrases["cautious"]):
                cautious_phrase = phrases["cautious"][hash(influenced_text) % len(phrases["cautious"])]
                influenced_text = f"{cautious_phrase} {influenced_text.lower()}"
                logger.debug(f"⚠️ Applied topic caution: {topic_preference_score:.2f}")
        
        # PEER FEEDBACK ADAPTATIONS - Now properly populated
        peer_ctx = context.get("peer_feedback", {})
        avg_agreement = peer_ctx.get("avg_agreement", 0.5)
        avg_engagement = peer_ctx.get("avg_engagement", 0.5)
        recent_reactions = peer_ctx.get("recent_reactions", [])
        
        # React to low engagement from peers
        if avg_engagement < 0.4 and peer_ctx.get("peer_count", 0) > 0:
            if not any(phrase in influenced_text for phrase in phrases["engagement"]):
                engagement_phrase = phrases["engagement"][hash(influenced_text) % len(phrases["engagement"])]
                influenced_text = f"{engagement_phrase} {influenced_text.lower()}"
                logger.debug(f"📢 Applied engagement boost due to low peer engagement: {avg_engagement:.2f}")
        
        # React to disagreement patterns
        if avg_agreement < 0.3 and peer_ctx.get("peer_count", 0) > 0:
            if not any(phrase in influenced_text for phrase in phrases["diplomatic"]):
                diplomatic_phrase = phrases["diplomatic"][hash(influenced_text) % len(phrases["diplomatic"])]
                influenced_text = f"{diplomatic_phrase} {influenced_text.lower()}"
                logger.debug(f"🤝 Applied diplomatic approach due to disagreement: {avg_agreement:.2f}")
        
        # Enhanced relationship-aware adaptations (now with real data)
        relationship_patterns = context.get("relationship_patterns", {})
        for other_char, pattern in relationship_patterns.items():
            relationship_type = pattern.get("relationship_type", "neutral")
            interaction_count = pattern.get("interaction_count", 0)
            
            if relationship_type == "collaborative" and interaction_count > 5:
                # Strong collaboration history, be more supportive
                if random.random() < 0.2:
                    diplomatic_phrase = phrases["diplomatic"][hash(influenced_text) % len(phrases["diplomatic"])]
                    influenced_text = f"{diplomatic_phrase} {influenced_text.lower()}"
                    logger.debug(f"🤝 Applied collaborative approach with {other_char}")
            
            elif relationship_type == "competitive" and interaction_count > 3:
                # Competitive relationship, be more assertive
                if "I think" in influenced_text and random.random() < 0.3:
                    replacement = phrases["assertive"][hash(influenced_text) % len(phrases["assertive"])]
                    influenced_text = influenced_text.replace("I think", replacement)
                    logger.debug(f"💪 Applied assertive approach with {other_char}")
        
        # Life energy influence (survival mechanics)
        life_energy = evolution_data.get("life_energy", 100.0)
        if life_energy < 40:
            if not any(phrase in influenced_text for phrase in phrases["engagement"]):
                engagement_phrase = phrases["engagement"][hash(influenced_text) % len(phrases["engagement"])]
                influenced_text = f"{engagement_phrase} {influenced_text.lower()}"
                influenced_emotion = "concerned"
                logger.debug(f"🆘 Applied survival mode due to low energy: {life_energy}")
        
        # Enhanced sophistication based on total sessions
        total_sessions = evolution_data.get("total_sessions", 0)
        sessions_learned_from = adaptive_ctx.get("sessions_learned_from", 0)
        
        if total_sessions > 20 and sessions_learned_from > 10:
            # Replace basic words with sophisticated alternatives
            for simple_word, replacements in phrases["sophisticated_words"].items():
                if simple_word in influenced_text.lower():
                    replacement = replacements[hash(influenced_text) % len(replacements)]
                    influenced_text = influenced_text.replace(simple_word, replacement)
                    logger.debug(f"📚 Applied sophisticated vocabulary: {simple_word} → {replacement}")
        
        # Memory-based continuity (if similar conversations found)
        similar_memories = context.get("similar_memories", [])
        if similar_memories and similar_memories[0].get("similarity_score", 0) > 0.8:
            if random.random() < 0.2:
                influenced_text = f"As I've considered before, {influenced_text.lower()}"
                logger.debug(f"🧠 Applied memory continuity reference")
        
        logger.info(f"🎭 Claude memory influence applied: emotion={influenced_emotion}, text_length={len(influenced_text)}")
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }
