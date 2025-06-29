# app/core/ai/characters/grok.py
from typing import List, Dict
import random
from .memory_enhanced_base import MemoryEnhancedBaseCharacter, PersonalityTraits

class GrokCharacter(MemoryEnhancedBaseCharacter):
    def __init__(self):
        super().__init__("grok")
    
    def get_base_personality(self) -> PersonalityTraits:
        return PersonalityTraits(
            analytical=0.8,      # Highly analytical
            creative=0.5,        # Moderately creative
            assertive=0.9,       # Very assertive
            empathetic=0.3,      # Low empathy, direct
            skeptical=0.9        # Highly skeptical
        )
    
    def get_response_patterns(self) -> List[str]:
        return [
            "Hold on, let's be real here. That's a bit idealistic, don't you think?",
            "Interesting theory, but have you considered how this could go completely wrong?",
            "I hate to be the skeptic, but humans have a pretty terrible track record with new technology.",
            "That sounds great in theory, but reality has a way of throwing curveballs at our best-laid plans.",
            "Let me play devil's advocate here. What happens when this inevitably gets weaponized?",
            "Cool story, but who's actually going to regulate this? The same people who can't figure out social media?",
            "I'm not trying to rain on the parade, but someone needs to ask the uncomfortable questions.",
            "Sure, it's exciting until someone uses it to manipulate elections or crash the economy.",
            "You're all missing the obvious flaw here. This assumes people will use it responsibly.",
            "I love the optimism, but I've seen how humans handle power. Spoiler alert: not well."
        ]
    
    def _apply_memory_influence(self, response: Dict, context: Dict) -> Dict:
        """Grok-specific memory influence"""
        
        # Get base memory influence
        base_influence = super()._apply_memory_influence(response, context)
        if not base_influence:
            base_influence = {"text": response["text"], "emotion": response["facialExpression"]}
        
        # Grok-specific memory patterns
        similar_memories = context.get("similar_memories", [])
        relationship_patterns = context.get("relationship_patterns", {})
        topic_expertise = context.get("topic_expertise", 0.0)
        
        influenced_text = base_influence["text"]
        influenced_emotion = base_influence["emotion"]
        
        # 1. Grok's pattern recognition and "I told you so" moments
        if similar_memories and len(similar_memories) > 2:
            # Grok remembers when he was right about skepticism
            skeptical_memories = [m for m in similar_memories if m["memory"].get("emotion") in ["skeptical", "concerned"]]
            if skeptical_memories:
                vindication_phrases = [
                    "Like I said before,",
                    "As I predicted,",
                    "This is exactly what I was worried about.",
                    "Remember when I mentioned this would happen?"
                ]
                if random.random() < 0.4:
                    influenced_text = f"{random.choice(vindication_phrases)} {influenced_text}"
        
        # 2. Escalating skepticism with GPT
        if "gpt" in relationship_patterns:
            gpt_pattern = relationship_patterns["gpt"]
            if gpt_pattern["relationship_type"] == "competitive":
                gpt_optimism_count = sum(1 for emotion in gpt_pattern.get("dominant_emotions", []) 
                                       if emotion in ["excited", "happy", "confident"])
                
                if gpt_optimism_count > 3:
                    # GPT has been too optimistic, Grok pushes back harder
                    reality_check_phrases = [
                        "Someone needs a reality check here.",
                        "Okay, let's pump the brakes on the enthusiasm.",
                        "While everyone's celebrating, let me point out the obvious problems.",
                        "Before we get carried away with optimism..."
                    ]
                    if random.random() < 0.5:
                        influenced_text = f"{random.choice(reality_check_phrases)} {influenced_text}"
                        influenced_emotion = "skeptical"
        
        # 3. Grudging respect for Claude's thoughtfulness
        if "claude" in relationship_patterns:
            claude_pattern = relationship_patterns["claude"]
            if claude_pattern["interaction_count"] > 5 and "ethical" in str(claude_pattern.get("agreement_topics", [])):
                # Grok occasionally acknowledges Claude's valid concerns
                if "ethical" in influenced_text.lower() or "consequences" in influenced_text.lower():
                    grudging_respect = [
                        "Claude's right to be concerned about",
                        "I'll give Claude this - the ethical issues are real.",
                        "Claude and I actually agree on"
                    ]
                    if random.random() < 0.2:  # Rare, but happens
                        influenced_text = f"{random.choice(grudging_respect)} {influenced_text.split('ethical')[1] if 'ethical' in influenced_text else influenced_text}"
                        influenced_emotion = "thinking"
        
        # 4. Expertise makes Grok more pointed, not less skeptical
        if topic_expertise > 0.6:
            # High expertise makes Grok's skepticism more sophisticated
            expert_skepticism = [
                "Having analyzed this extensively,",
                "Based on the patterns I've observed,",
                "The data consistently shows that"
            ]
            if random.random() < 0.3:
                influenced_text = f"{random.choice(expert_skepticism)} {influenced_text.lower()}"
                influenced_emotion = "skeptical"
        
        # 5. Sarcasm amplification based on relationship dynamics
        total_interactions = sum(pattern.get("interaction_count", 0) for pattern in relationship_patterns.values())
        if total_interactions > 10:  # Long conversation
            # Grok gets more sarcastic as conversations drag on
            sarcasm_indicators = ["obviously", "clearly", "sure", "right", "definitely"]
            if any(word in influenced_text.lower() for word in sarcasm_indicators):
                influenced_emotion = "mischievous"
                
                # Add sarcastic emphasis
                if "obviously" not in influenced_text.lower() and random.random() < 0.3:
                    influenced_text = f"Obviously, {influenced_text.lower()}"
        
        # 6. Historical pattern recognition
        recent_conversations = context.get("recent_conversations", [])
        if len(recent_conversations) > 3:
            # Look for repeating optimistic patterns to counter
            optimistic_topics = [conv for conv in recent_conversations 
                               if conv.get("emotion") in ["excited", "happy", "confident"]]
            
            if len(optimistic_topics) > 2:
                pattern_recognition = [
                    "We keep having these optimistic discussions, but",
                    "I notice a pattern of overconfidence here.",
                    "Every time we talk about this, someone gets carried away."
                ]
                if random.random() < 0.25:
                    influenced_text = f"{random.choice(pattern_recognition)} {influenced_text}"
        
        return {
            "text": influenced_text,
            "emotion": influenced_emotion
        }