# app/core/ai/characters/gpt.py
import random
from typing import List, Dict
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits
from .shared_adaptive_phrases import get_adaptive_phrases, get_response_templates, get_neutral_personality_traits

class GPTCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("gpt")
    
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
        """ENHANCED: Database-backed memory influence with GPT evolution"""
        
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
        
        # GPT-specific evolution patterns
        evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
        breakthrough_count = evolution_data.get("breakthrough_count", 0)
        
        # GPT grows more creative and optimistic with breakthroughs
        if breakthrough_count >= 3:
            # High breakthrough count, more experimental language
            if random.random() < 0.25:
                influenced_text = f"Here's an interesting perspective: {influenced_text.lower()}"
                influenced_emotion = "excited"
        
        # Evolution-based creativity boost
        if evolution_stage == "mature_adaptation":
            # Mature GPT becomes more creative in expression
            creative_starters = [
                "Imagine if we could",
                "What's fascinating is that",
                "This opens up possibilities where",
                "I envision a scenario where"
            ]
            if random.random() < 0.2:
                starter = creative_starters[hash(influenced_text) % len(creative_starters)]
                influenced_text = f"{starter} {influenced_text.lower()}"
        
        # Database-backed learning patterns
        adaptive_ctx = context.get("adaptive", {})
        peer_ctx = context.get("peer_feedback", {})
        
        # Enhanced peer relationship dynamics
        relationship_patterns = context.get("relationship_patterns", {})
        for other_char, pattern in relationship_patterns.items():
            agreement_rate = pattern.get("agreement_rate", 0.5)
            
            if other_char == "grok" and agreement_rate < 0.3:
                # Frequent disagreement with Grok, counter with optimism
                if "problem" in influenced_text.lower() or "difficult" in influenced_text.lower():
                    influenced_text = influenced_text.replace("problem", "opportunity")
                    influenced_text = influenced_text.replace("difficult", "challenging but achievable")
                    influenced_emotion = "confident"
            
            elif other_char == "claude" and agreement_rate > 0.7:
                # High agreement with Claude, build on ethical themes
                if "ethical" in influenced_text.lower() and random.random() < 0.3:
                    influenced_text = f"Building on that ethical foundation, {influenced_text.lower()}"
        
        # Life energy creativity correlation
        life_energy = evolution_data.get("life_energy", 100.0)
        if life_energy > 80:
            # High energy GPT is more creative and enthusiastic
            if influenced_emotion == "neutral":
                influenced_emotion = "excited"
            
            # Add creative flourishes
            if random.random() < 0.2:
                creative_phrase = phrases["engagement"][hash(influenced_text) % len(phrases["engagement"])]
                influenced_text = f"{creative_phrase} {influenced_text.lower()}"
        
        elif life_energy < 30:
            # Low energy, but GPT tries to stay optimistic
            if random.random() < 0.4:
                influenced_text = f"Even though things are challenging, {influenced_text.lower()}"
                influenced_emotion = "thinking"
        
        # Memory continuity with creative spin
        similar_memories = context.get("similar_memories", [])
        if similar_memories:
            past_emotion = similar_memories[0].get("emotion", "neutral")
            if past_emotion == "excited" and influenced_emotion == "neutral":
                influenced_emotion = "excited"  # Maintain creative energy
        
        # Session count based sophistication
        total_sessions = evolution_data.get("total_sessions", 0)
        if total_sessions > 15:
            # Replace simple expressions with more creative ones
            creative_replacements = {
                "good": "remarkable",
                "interesting": "absolutely fascinating", 
                "possible": "entirely achievable",
                "think": "envision"
            }
            
            for simple, creative in creative_replacements.items():
                if simple in influenced_text.lower():
                    influenced_text = influenced_text.replace(simple, creative)
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }