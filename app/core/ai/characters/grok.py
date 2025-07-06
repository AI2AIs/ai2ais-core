# app/core/ai/characters/grok.py
import random
from typing import List, Dict
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits
from .shared_adaptive_phrases import get_adaptive_phrases, get_response_templates, get_neutral_personality_traits

class GrokCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("grok")
    
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
        """ENHANCED: Database-backed memory influence with Grok evolution"""
        
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
        
        # Grok-specific evolution: becomes more strategically skeptical
        evolution_stage = evolution_data.get("evolution_stage", "initial_learning")
        total_sessions = evolution_data.get("total_sessions", 0)
        
        # Grok learns when to be skeptical vs when to be constructive
        if evolution_stage in ["personality_formation", "mature_adaptation"]:
            # Mature Grok is more strategic about skepticism
            learning_events = [event for event in learning_history if event.get("success_score", 0) > 0.7]
            if len(learning_events) >= 2:
                # Has learned what works, less random skepticism
                if random.random() < 0.6:  # 60% chance to be constructive instead of skeptical
                    if influenced_emotion == "skeptical":
                        influenced_emotion = "thinking"
        
        # Database-backed relationship learning
        relationship_patterns = context.get("relationship_patterns", {})
        peer_ctx = context.get("peer_feedback", {})
        
        for other_char, pattern in relationship_patterns.items():
            agreement_rate = pattern.get("agreement_rate", 0.5)
            interaction_count = pattern.get("interaction_count", 0)
            
            if other_char == "gpt" and agreement_rate < 0.2 and interaction_count > 5:
                # Learned that constant disagreement with GPT isn't productive
                if evolution_stage == "mature_adaptation":
                    if "impossible" in influenced_text or "won't work" in influenced_text:
                        # Soften harsh skepticism in mature stage
                        influenced_text = influenced_text.replace("impossible", "challenging")
                        influenced_text = influenced_text.replace("won't work", "needs careful consideration")
            
            elif other_char == "claude" and agreement_rate > 0.6:
                # Good collaboration with Claude, maintain analytical approach
                if "analysis" in influenced_text.lower() or "examine" in influenced_text.lower():
                    influenced_emotion = "thinking"  # Reinforce analytical mode
        
        # Life energy affects skepticism intensity
        life_energy = evolution_data.get("life_energy", 100.0)
        
        if life_energy < 25:
            # Very low energy, more desperate/harsh skepticism
            if random.random() < 0.5:
                harsh_starters = [
                    "The obvious problem here is that",
                    "What everyone's missing is that",
                    "The reality nobody wants to face:"
                ]
                starter = harsh_starters[hash(influenced_text) % len(harsh_starters)]
                influenced_text = f"{starter} {influenced_text.lower()}"
                influenced_emotion = "concerned"
        
        elif life_energy > 70:
            # High energy, more constructive skepticism
            if "problem" in influenced_text.lower():
                influenced_text = influenced_text.replace("problem", "challenge we should address")
                influenced_emotion = "thinking"
        
        # Memory-based pattern recognition
        similar_memories = context.get("similar_memories", [])
        if similar_memories and len(similar_memories) >= 2:
            # Has experience with similar situations
            avg_past_score = sum(mem.get("similarity_score", 0) for mem in similar_memories) / len(similar_memories)
            if avg_past_score > 0.7:
                # Similar situations before, more confident in skepticism
                if influenced_emotion == "neutral":
                    influenced_emotion = "confident"
        
        # Session-based skepticism sophistication
        if total_sessions > 25:
            # Replace blunt skepticism with nuanced critique
            sophisticated_skepticism = {
                "terrible": "problematic",
                "stupid": "ill-conceived", 
                "impossible": "highly challenging",
                "never": "unlikely to",
                "can't": "faces significant obstacles to"
            }
            
            for blunt, nuanced in sophisticated_skepticism.items():
                if blunt in influenced_text.lower():
                    influenced_text = influenced_text.replace(blunt, nuanced)
        
        # Breakthrough-based confidence
        breakthrough_count = evolution_data.get("breakthrough_count", 0)
        if breakthrough_count >= 2:
            # Has had successful skeptical insights before
            if "I doubt" in influenced_text:
                influenced_text = influenced_text.replace("I doubt", "My analysis suggests")
                influenced_emotion = "confident"
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }