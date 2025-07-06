# app/core/ai/characters/shared_adaptive_phrases.py
"""
Shared adaptive phrases for ALL characters - guarantees complete neutrality
Every character uses EXACTLY the same phrase pools to ensure no predefined bias
"""

def get_adaptive_phrases():
    """
    Returns all adaptive phrase pools used by characters
    This ensures 100% identical phrase availability for all characters
    """
    return {
        # 1. Cautious phrases (when failed in topic before)
        "cautious": [
            "I need to think about",
            "This requires consideration:",
            "Let me examine this:",
            "I should consider",
            "This needs careful thought:",
            "I want to be thoughtful about",
            "Let me reflect on",
            "This deserves attention:"
        ],
        
        # 2. Assertive phrases (when peers agree highly)
        "assertive": [
            "I'm certain that",
            "I believe that", 
            "I'm convinced that",
            "It's clear that",
            "I'm confident that",
            "Without doubt,",
            "I firmly believe",
            "I'm sure that"
        ],
        
        # 3. Engagement boosters (when boring/low engagement)
        "engagement": [
            "Here's what's interesting:",
            "This brings up an important point:",
            "There's something significant here:",
            "What stands out to me is:",
            "Here's what's fascinating:",
            "This is particularly noteworthy:",
            "What's compelling about this is:",
            "The key insight here is:"
        ],
        
        # 4. Contrarian phrases (when too much agreement)
        "contrarian": [
            "Let me offer a different view:",
            "I see this differently:",
            "Consider this alternative:",
            "What if we approached this differently:",
            "I have a different perspective:",
            "Let me challenge this:",
            "Here's another way to look at it:",
            "I'd like to present a different angle:"
        ],
        
        # 5. Competitive phrases (for competitive relationships)
        "competitive": [
            "I disagree with the premise that",
            "That's not quite right because",
            "I see a flaw in this thinking:",
            "Let me challenge this idea:",
            "I have to respectfully disagree:",
            "There's an issue with this approach:",
            "I question whether",
            "I'm not convinced that"
        ],
        
        # 6. Provocative starters (when very low engagement)
        "provocative": [
            "Here's what nobody talks about:",
            "What everyone's missing is:",
            "The real issue here is:",
            "Let's be honest about this:",
            "The elephant in the room is:",
            "What people don't realize is:",
            "The uncomfortable truth is:",
            "Here's what's really happening:"
        ],
        
        # 7. Expansion phrases (when response too short)
        "expansion": [
            "Furthermore,",
            "Additionally,", 
            "What's more,",
            "Beyond that,",
            "Moreover,",
            "In addition,",
            "Also important is that",
            "It's also worth noting that"
        ],
        
        # 8. Diplomatic phrases (when relationships need smoothing)
        "diplomatic": [
            "I understand the perspective that",
            "While I see the merit in",
            "I appreciate the point about",
            "There's validity to the idea that",
            "I can see how",
            "It's worth considering that",
            "I recognize the argument for",
            "There's wisdom in"
        ],
        
        # 9. Sophisticated word replacements (when character matures)
        "sophisticated_words": {
            "good": ["beneficial", "valuable", "effective", "worthwhile", "advantageous"],
            "bad": ["problematic", "concerning", "detrimental", "counterproductive", "harmful"],
            "big": ["significant", "substantial", "considerable", "major", "extensive"],
            "small": ["minimal", "modest", "limited", "minor", "negligible"],
            "important": ["crucial", "vital", "essential", "critical", "pivotal"],
            "interesting": ["compelling", "fascinating", "intriguing", "thought-provoking", "remarkable"],
            "easy": ["straightforward", "accessible", "manageable", "simple", "effortless"],
            "hard": ["challenging", "complex", "demanding", "difficult", "intricate"],
            "fast": ["rapid", "swift", "quick", "expeditious", "prompt"],
            "slow": ["gradual", "measured", "deliberate", "methodical", "steady"]
        },
        
        # 10. Confidence boosters (when successful in topic)
        "confidence": [
            "Based on my experience with this,",
            "Having explored this extensively,",
            "From my understanding of this subject,",
            "Given my familiarity with this topic,",
            "Drawing from my knowledge here,",
            "With my background in this area,",
            "From what I've learned about this,",
            "Having studied this previously,"
        ],
        
        # 11. Uncertainty expressions (when new/unknown topic)
        "uncertainty": [
            "I'm still learning about",
            "This is new territory for me:",
            "I'm exploring this concept:",
            "I'm developing my understanding of",
            "This challenges my current thinking:",
            "I'm working through",
            "I'm grappling with",
            "This raises questions for me about"
        ]
    }

def get_response_templates():
    """
    Returns identical response templates for ALL characters
    Ensures no character-specific response patterns
    """
    return [
        "I think this is {sentiment}.",
        "My view on this is {opinion}.",
        "This makes me {emotion}.",
        "When I consider this, I {reaction}.",
        "From my perspective, {analysis}.",
        "I find this {assessment}.",
        "This brings up {thought} for me.",
        "My response is {response}.",
        "I {agreement_level} with this.",
        "This concept {evaluation} to me."
    ]

def get_neutral_personality_traits():
    """
    Returns completely neutral personality traits for ALL characters
    Ensures identical starting point
    """
    return {
        "analytical": 0.5,    # Neutral - will learn
        "creative": 0.5,      # Neutral - will learn  
        "assertive": 0.5,     # Neutral - will learn
        "empathetic": 0.5,    # Neutral - will learn
        "skeptical": 0.5      # Neutral - will learn
    }