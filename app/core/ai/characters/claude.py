# app/core/ai/characters/claude.py
from typing import List
from .base import BaseCharacter, PersonalityTraits

class ClaudeCharacter(BaseCharacter):
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