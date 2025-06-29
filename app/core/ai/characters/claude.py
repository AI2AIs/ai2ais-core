# app/core/ai/characters/claude.py
from typing import List, Dict
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits

class ClaudeCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("claude")
    
    def get_base_personality(self) -> PersonalityTraits:
        return PersonalityTraits(
            analytical=0.9,      # Very analytical
            creative=0.6,        # Moderately creative  
            assertive=0.4,       # Gentle, not too assertive
            empathetic=0.8,      # Highly empathetic
            skeptical=0.3        # Generally optimistic
        )
    
    def get_response_patterns(self) -> List[str]:
        return [
            "That's a fascinating perspective. I think we need to consider the ethical implications more deeply.",
            "I appreciate the nuance in this discussion. From my understanding, the complexity lies in how we define consciousness itself.",
            "While I see the merit in that argument, I'd like to explore the potential consequences for society.",
            "This reminds me of philosophical questions about the nature of identity and what makes us human.",
            "I think there's wisdom in approaching this with both optimism and caution.",
            "The intersection of technology and ethics here is particularly intriguing.",
            "We should consider multiple perspectives before drawing conclusions.",
            "I'm curious about the long-term implications of this line of thinking.",
            "There's something beautiful about the complexity of this question.",
            "Perhaps we're asking the wrong question entirely. What if we reframed this as..."
        ]
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Dict:
        """Claude-specific memory influence"""
        
        # Get base memory influence
        base_influence = super()._apply_memory_influence(response, context)
        if not base_influence:
            base_influence = {"text": response["text"], "emotion": response["facialExpression"]}
        
        # Claude-specific memory patterns
        similar_memories = context.get("similar_memories", [])
        relationship_patterns = context.get("relationship_patterns", {})
        
        influenced_text = base_influence["text"]
        influenced_emotion = base_influence["emotion"]
        
        # 1. Claude's thoughtful referencing style
        if similar_memories and len(similar_memories) > 1:
            # Claude tends to synthesize multiple perspectives
            claude_synthesis = [
                "Building on our previous discussions,",
                "Considering what we've explored before,",
                "Reflecting on our ongoing conversation about this,"
            ]
            if "Building" not in influenced_text and "Considering" not in influenced_text:
                influenced_text = f"{claude_synthesis[0]} {influenced_text}"
        
        # 2. Relationship-aware empathy
        if "gpt" in relationship_patterns:
            gpt_pattern = relationship_patterns["gpt"]
            if gpt_pattern["relationship_type"] == "collaborative":
                # Claude appreciates GPT's creativity
                empathy_phrases = [
                    "I find myself inspired by the creative approaches we've discussed.",
                    "The innovative perspectives shared here continue to intrigue me."
                ]
                if any(word in influenced_text.lower() for word in ["creative", "innovative", "imagine"]):
                    influenced_text = f"{empathy_phrases[0]} {influenced_text}"
        
        # 3. Claude's cautious optimism with expertise
        topic_expertise = context.get("topic_expertise", 0.0)
        if topic_expertise > 0.6:
            # High expertise -> more confident but still measured
            influenced_emotion = "thinking" if influenced_emotion == "neutral" else influenced_emotion
            
            if "ethical" in influenced_text.lower() or "implications" in influenced_text.lower():
                influenced_emotion = "concerned"
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }