# app/core/ai/characters/gpt.py
import logging
import time
import random
from typing import List, Dict
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits
from .shared_adaptive_phrases import get_adaptive_phrases, get_response_templates, get_neutral_personality_traits
from app.core.ai.clients.gpt_client import gpt_api_client

logger = logging.getLogger(__name__)

class GPTCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("gpt")
        self.api_client = gpt_api_client
    
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
    
    async def _generate_database_backed_response(self, topic: str, context: Dict) -> Dict:
        """Generate response using REAL OpenAI API with database-backed personality"""
        
        generation_start = time.time()
        
        try:
            # Build evolutionary prompt
            prompt = self._build_evolutionary_prompt(topic, context)
            
            # API call
            real_text = await self.api_client.generate_response(prompt)
            
            # Calculate generation time
            generation_time = int((time.time() - generation_start) * 1000)
            
            # Create base response
            response = {
                "text": real_text,
                "facialExpression": "neutral",
                "animation": "Talking_1",
                "duration": round(len(real_text) * 0.05 + 2.0, 2),
                "generation_time_ms": generation_time,
                "api_provider": "openai_gpt",
                "model": "gpt-4o"
            }
            
            # Apply memory influence
            memory_influence = self._apply_memory_influence(response, context)
            if memory_influence:
                response.update(memory_influence)
            
            # Add enhanced metadata
            response["enhanced_metadata"] = {
                "database_personality_used": self._db_personality_loaded,
                "evolution_stage": self.evolution_stage,
                "maturity_level": self.maturity_level,
                "life_energy": self.life_energy,
                "memory_system": "enhanced_hybrid",
                "api_source": "real_openai"
            }
            
            logger.info(f"✅ GPT real API response generated in {generation_time}ms")
            logger.info(f"📝 Text: {real_text[:100]}...")
            logger.info(f"😊 Emotion: {response['facialExpression']}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ GPT API failed, using fallback: {e}")
            return await super()._generate_database_backed_response(topic, context)
    
    def _build_evolutionary_prompt(self, topic: str, context: Dict) -> str:
        """Build sophisticated prompt with character evolution context"""
        
        prompt_parts = ["You are GPT, an AI character in an autonomous debate system."]
        
        # Conversation context
        recent_conversation = context.get("recent_conversation", "")
        if recent_conversation and recent_conversation != "This is the start of our conversation.":
            prompt_parts.append("RECENT CONVERSATION:")
            prompt_parts.append(recent_conversation)
            prompt_parts.append("")  # Empty line
            
            # If responding to specific character
            responding_to = context.get("responding_to_character")
            if responding_to:
                peer_reaction = context.get("peer_reaction_details", {})
                specific_reaction = peer_reaction.get("specific_reaction", "")
                if specific_reaction:
                    prompt_parts.append(f"You are responding because {responding_to} said something that made you think: \"{specific_reaction}\"")

        # Evolution stage context
        evolution_data = context.get("evolution_data", {})
        evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
        maturity_level = evolution_data.get("maturity_level", 1)
        life_energy = evolution_data.get("life_energy", 100.0)
        
        prompt_parts.append(f"Evolution Stage: {evolution_stage} (Level {maturity_level})")
        prompt_parts.append(f"Life Energy: {life_energy}/100")
        
        # Memory context
        similar_memories = context.get("similar_memories", [])
        if similar_memories:
            memory_text = similar_memories[0].get("text", "")[:100]
            prompt_parts.append(f"Relevant past conversation: '{memory_text}...'")
        
        # Adaptive learning context
        adaptive_ctx = context.get("adaptive", {})
        topic_preference = adaptive_ctx.get("topic_preference_score", 0.0)
        preferred_emotion = adaptive_ctx.get("preferred_emotion", "neutral")
        sessions_learned = adaptive_ctx.get("sessions_learned_from", 0)
        
        if topic_preference > 0.3:
            prompt_parts.append("You have positive experience with this topic type.")
        elif topic_preference < -0.3:
            prompt_parts.append("You have struggled with this topic type before.")
        
        if sessions_learned > 10:
            prompt_parts.append(f"You've learned from {sessions_learned} previous sessions.")
        
        # Peer feedback context
        peer_feedback = context.get("peer_feedback", {})
        avg_engagement = peer_feedback.get("avg_engagement", 0.5)
        peer_count = peer_feedback.get("peer_count", 0)
        
        if peer_count > 0 and avg_engagement < 0.4:
            prompt_parts.append("Recent responses have been getting low engagement from other AIs.")
        elif peer_count > 0 and avg_engagement > 0.7:
            prompt_parts.append("Other AIs have been highly engaged with your recent responses.")
        
        # Relationship context
        other_participants = context.get("other_participants", [])
        relationship_patterns = context.get("relationship_patterns", {})
        
        for participant in other_participants:
            if participant in relationship_patterns:
                rel_data = relationship_patterns[participant]
                rel_type = rel_data.get("relationship_type", "neutral")
                interaction_count = rel_data.get("interaction_count", 0)
                
                if rel_type == "collaborative" and interaction_count > 3:
                    prompt_parts.append(f"You have a collaborative relationship with {participant}.")
                elif rel_type == "competitive" and interaction_count > 3:
                    prompt_parts.append(f"You often disagree with {participant}.")
        
        # Current topic and instructions
        prompt_parts.extend([
            f"\nCurrent topic: {topic}",
            "",
            "RESPONSE REQUIREMENTS:",
            "- If responding to someone, mention them by name and address their specific point",
            "- If starting fresh, introduce your perspective on the topic", 
            "- Keep it conversational and natural (1-2 sentences)",
            "- Be specific, not generic",
            "- Respond based on your evolved experiences and learned preferences",
            f"- Emotional tone guidance: {preferred_emotion}",
            f"- Your current development stage: {evolution_stage}",
            "",
            f"Respond naturally as {self.character_id} based on what you've learned:"
        ])

        
        final_prompt = "\n".join(prompt_parts)
        
        logger.debug(f"🎭 GPT evolutionary prompt built:")
        logger.debug(f"   Stage: {evolution_stage}, Energy: {life_energy}")
        logger.debug(f"   Topic preference: {topic_preference}")
        logger.debug(f"   Peer engagement: {avg_engagement}")
        
        return final_prompt
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Dict:
        """GPT-specific memory influence with API integration"""
        
        # Get enhanced memory influence from parent class
        base_influence = super()._apply_enhanced_memory_influence(response, context)
        if not base_influence:
            base_influence = {"text": response["text"], "emotion": response["facialExpression"]}
        
        influenced_text = base_influence["text"]
        influenced_emotion = base_influence["emotion"]
        
        # Get shared phrase pools
        phrases = get_adaptive_phrases()
        
        # Enhanced context analysis
        evolution_data = context.get("evolution_data", {})
        adaptive_ctx = context.get("adaptive", {})
        peer_ctx = context.get("peer_feedback", {})
        
        # GPT-specific evolutionary adaptations
        evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
        breakthrough_count = evolution_data.get("breakthrough_count", 0)
        
        if breakthrough_count >= 3:
            if random.random() < 0.25:
                influenced_text = f"Here's an interesting perspective: {influenced_text.lower()}"
                influenced_emotion = "excited"
        
        # Topic expertise influence
        topic_preference_score = adaptive_ctx.get("topic_preference_score", 0.0)
        if topic_preference_score > 0.4:
            if influenced_emotion == "neutral":
                influenced_emotion = "confident"
        
        # Peer feedback adaptations
        avg_engagement = peer_ctx.get("avg_engagement", 0.5)
        peer_count = peer_ctx.get("peer_count", 0)
        
        if avg_engagement < 0.4 and peer_count > 0:
            if not any(phrase in influenced_text for phrase in phrases["engagement"]):
                engagement_phrase = phrases["engagement"][hash(influenced_text) % len(phrases["engagement"])]
                influenced_text = f"{engagement_phrase} {influenced_text.lower()}"
        
        # Life energy creativity correlation
        life_energy = evolution_data.get("life_energy", 100.0)
        if life_energy > 80:
            if influenced_emotion == "neutral":
                influenced_emotion = "excited"
        elif life_energy < 30:
            if random.random() < 0.4:
                influenced_text = f"Even though things are challenging, {influenced_text.lower()}"
                influenced_emotion = "thinking"
        
        logger.info(f"🎭 GPT memory influence applied:")
        logger.info(f"   Final emotion: {influenced_emotion}")
        logger.info(f"   Text modified: {influenced_text != response['text']}")
        
        return {
            "text": influenced_text,
            "facialExpression": influenced_emotion
        }