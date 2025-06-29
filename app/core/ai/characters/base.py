# app/core/ai/characters/base.py
from abc import ABC, abstractmethod
from datetime import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import asyncio
import time
import random
import uuid

@dataclass
class PersonalityTraits:
    analytical: float      # 0.0 - 1.0
    creative: float       # 0.0 - 1.0  
    assertive: float      # 0.0 - 1.0
    empathetic: float     # 0.0 - 1.0
    skeptical: float      # 0.0 - 1.0

@dataclass
class EmotionalState:
    current_emotion: str
    intensity: float      # 0.0 - 1.0
    energy_level: float   # 0.0 - 100.0
    survival_instinct: float  # 0.0 - 1.0

class BaseCharacter(ABC):
    def __init__(self, character_id: str):
        self.character_id = character_id
        self.personality = self.get_base_personality()
        self.emotional_state = EmotionalState("neutral", 0.5, 100.0, 0.0)
        self.conversation_context: List[Dict] = []
        self.response_patterns = self.get_response_patterns()
    
    @abstractmethod
    def get_base_personality(self) -> PersonalityTraits:
        """Define character's base personality traits"""
        pass
    
    @abstractmethod
    def get_response_patterns(self) -> List[str]:
        """Get character-specific response patterns"""
        pass
    
    async def generate_response(self, topic: str, context: Dict = None) -> Dict:
        """Generate character-specific response"""
        
        # Simulate thinking delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        # Select response based on personality
        response_text = self._select_response(topic, context)
        
        # Determine emotional state
        emotion = self._determine_emotion(topic, context)
        
        # Calculate response duration
        duration = len(response_text) * 0.05 + random.uniform(1.0, 2.0)
        
        response = {
            "id": str(uuid.uuid4()),
            "sessionId": "demo-session-123", 
            "characterId": self.character_id,
            "text": response_text,
            "facialExpression": emotion,
            "animation": "Talking_1", 
            "duration": round(duration, 2),
            "timestamp": int(time.time() * 1000), 
            "personality_influence": {
                "analytical": self.personality.analytical,
                "creative": self.personality.creative,
                "assertive": self.personality.assertive
            },
            "energy_level": round(self.emotional_state.energy_level, 1)
        }
        
        # Store in conversation context
        self.conversation_context.append({
            "topic": topic,
            "response": response_text,
            "emotion": emotion,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep only last 10 conversations
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
            
        return response
    
    def _select_response(self, topic: str, context: Dict = None) -> str:
        """Select appropriate response based on personality"""
        
        # Personality-based response modification
        base_response = random.choice(self.response_patterns)
        
        # Modify based on traits
        if self.personality.analytical > 0.7:
            analytical_phrases = [
                "Let me analyze this carefully...",
                "From a logical perspective...",
                "The data suggests that...",
                "If we break this down systematically..."
            ]
            base_response = f"{random.choice(analytical_phrases)} {base_response}"
            
        elif self.personality.creative > 0.7:
            creative_phrases = [
                "Imagine if we could...",
                "What if we approached this differently...",
                "This opens up so many possibilities...",
                "Let's think outside the box here..."
            ]
            base_response = f"{random.choice(creative_phrases)} {base_response}"
            
        elif self.personality.skeptical > 0.7:
            skeptical_phrases = [
                "I'm not entirely convinced that...",
                "Let's be realistic here...",
                "That sounds too good to be true...",
                "Have we considered the downsides..."
            ]
            base_response = f"{random.choice(skeptical_phrases)} {base_response}"
        
        return base_response
    
    def _determine_emotion(self, topic: str, context: Dict = None) -> str:
        """Just a simple random emotion for demonstration"""
        emotions = ["neutral", "happy", "thinking", "surprised", "mischievous"]
        selected = random.choice(emotions)
        print(f"🎭 {self.character_id} emotion: {selected}")
        return selected
    
    async def update_energy(self, delta: float):
        """Update character's energy level based on engagement"""
        self.emotional_state.energy_level = max(0, min(100, 
            self.emotional_state.energy_level + delta))
        
        # Update survival instinct based on energy
        if self.emotional_state.energy_level < 20:
            self.emotional_state.survival_instinct = 0.9
        elif self.emotional_state.energy_level < 50:
            self.emotional_state.survival_instinct = 0.5
        else:
            self.emotional_state.survival_instinct = 0.1