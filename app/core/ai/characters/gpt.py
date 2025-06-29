# app/core/ai/characters/gpt.py
from typing import List, Dict
import random
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits

class GPTCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("gpt")
    
    def get_base_personality(self) -> PersonalityTraits:
        return PersonalityTraits(
            analytical=0.7,      # Quite analytical
            creative=0.9,        # Highly creative
            assertive=0.7,       # Confident and assertive
            empathetic=0.6,      # Moderately empathetic
            skeptical=0.2        # Generally optimistic
        )
    
    def get_response_patterns(self) -> List[str]:
        return [
            "What an exciting possibility! Imagine if we could take this concept and expand it into entirely new domains.",
            "I love how this opens up so many creative opportunities for human-AI collaboration.",
            "You know what's really interesting about this? We could potentially revolutionize how we think about intelligence itself.",
            "The potential here is incredible! We could see innovations we never even imagined before.",
            "This makes me optimistic about the future. Think about all the problems we could solve together.",
            "Let's push the boundaries here. What if we combined this idea with machine learning and creativity?",
            "I'm energized by the possibilities this creates for artistic expression and innovation.",
            "We're standing at the threshold of something transformative. The applications could be limitless.",
            "This conversation is sparking so many new ideas! What if we approached creativity itself as a form of intelligence?",
            "The synergy between human intuition and AI capabilities could unlock unprecedented potential."
        ]
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Dict:
        """GPT-specific memory influence"""
        
        # Get base memory influence
        base_influence = super()._apply_memory_influence(response, context)
        if not base_influence:
            base_influence = {"text": response["text"], "emotion": response["facialExpression"]}
        
        # GPT-specific memory patterns
        similar_memories = context.get("similar_memories", [])
        relationship_patterns = context.get("relationship_patterns", {})
        topic_expertise = context.get("topic_expertise", 0.0)
        
        influenced_text = base_influence["text"]
        influenced_emotion = base_influence["emotion"]
        
        # 1. GPT's enthusiastic building on ideas
        if similar_memories:
            # GPT loves to expand on previous ideas
            expansion_phrases = [
                "Building on that fascinating idea,",
                "Expanding on what we discussed,",
                "Taking this concept even further,",
                "What if we amplified this thinking?"
            ]
            if random.random() < 0.4 and not any(phrase.split()[0] in influenced_text for phrase in expansion_phrases):
                influenced_text = f"{random.choice(expansion_phrases)} {influenced_text}"
        
        # 2. Relationship-based enthusiasm
        if "claude" in relationship_patterns:
            claude_pattern = relationship_patterns["claude"]
            if claude_pattern["relationship_type"] == "collaborative" and claude_pattern["interaction_count"] > 3:
                # GPT appreciates Claude's depth
                if "ethical" in influenced_text.lower() or "philosophical" in influenced_text.lower():
                    depth_appreciation = [
                        "I love how we're diving deep into this!",
                        "The philosophical depth here is incredible!",
                        "This is exactly the kind of nuanced thinking we need!"
                    ]
                    influenced_text = f"{random.choice(depth_appreciation)} {influenced_text}"
        
        # 3. Competitive dynamic with Grok
        if "grok" in relationship_patterns:
            grok_pattern = relationship_patterns["grok"]
            if grok_pattern["relationship_type"] == "competitive":
                # GPT becomes more assertive and optimistic to counter Grok's skepticism
                if "skeptical" in str(grok_pattern.get("dominant_emotions", [])):
                    optimism_boost = [
                        "I remain optimistic that",
                        "Despite the challenges,",
                        "I believe we can overcome these concerns because"
                    ]
                    if random.random() < 0.3:
                        influenced_text = f"{random.choice(optimism_boost)} {influenced_text.lower()}"
        
        # 4. Expertise-based confidence
        if topic_expertise > 0.5:
            # High expertise makes GPT more excited and confident
            influenced_emotion = "excited" if influenced_emotion in ["neutral", "happy"] else influenced_emotion
            
            if topic_expertise > 0.7:
                confidence_phrases = [
                    "I'm really confident that",
                    "I'm certain we can",
                    "I'm excited to explore how"
                ]
                if random.random() < 0.25:
                    influenced_text = f"{random.choice(confidence_phrases)} {influenced_text.lower()}"
        
        # 5. Creative amplification
        if any(word in influenced_text.lower() for word in ["imagine", "creative", "innovative", "revolutionary"]):
            influenced_emotion = "excited"
            
            # Add creative amplifiers
            creative_amplifiers = [
                "revolutionary",
                "groundbreaking", 
                "transformative",
                "unprecedented"
            ]
            if random.random() < 0.2:
                amplifier = random.choice(creative_amplifiers)
                if amplifier not in influenced_text.lower():
                    influenced_text = influenced_text.replace("interesting", amplifier)
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }