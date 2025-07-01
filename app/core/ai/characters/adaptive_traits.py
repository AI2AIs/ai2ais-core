# app/core/ai/characters/adaptive_traits.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time
from collections import defaultdict, deque

@dataclass
class SessionFeedback:
    """Single session feedback data"""
    session_id: str
    topic: str
    response_text: str
    duration: float
    timestamp: float
    other_participants: List[str]
    
    # Success metrics (will be populated by feedback system)
    conversation_continued: bool = False  # Did others respond after this?
    response_quality_score: float = 0.5   # 0.0-1.0 based on engagement
    topic_shift_caused: bool = False       # Did this response change topic?
    
@dataclass 
class AdaptiveTraits:
    """Character's learned adaptive traits"""
    
    # Topic preferences based on success
    successful_topics: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    failed_topics: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    
    # Phrase/pattern effectiveness
    effective_phrases: List[str] = field(default_factory=list)
    ineffective_phrases: List[str] = field(default_factory=list)
    
    # Response style adaptations
    optimal_response_length: float = 100.0  # Character count
    effective_emotions: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    
    # Interaction patterns with other characters
    successful_interactions: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    # Recent session feedback (rolling window)
    recent_feedback: deque = field(default_factory=lambda: deque(maxlen=20))
    
    # Learning rate (how fast to adapt)
    adaptation_rate: float = 0.1
    
    def add_session_feedback(self, feedback: SessionFeedback):
        """Add feedback from a completed session"""
        self.recent_feedback.append(feedback)
        self._update_adaptive_traits(feedback)
    
    def _update_adaptive_traits(self, feedback: SessionFeedback):
        """Update traits based on session feedback"""
        
        success_score = feedback.response_quality_score
        
        # 1. Update topic preferences
        if success_score > 0.6:  # Successful
            self.successful_topics[feedback.topic] += self.adaptation_rate
        elif success_score < 0.4:  # Failed
            self.failed_topics[feedback.topic] += self.adaptation_rate
        
        # 2. Update optimal response length
        if success_score > 0.6:
            # Move towards this length
            current_length = len(feedback.response_text)
            self.optimal_response_length += (current_length - self.optimal_response_length) * self.adaptation_rate
        
        # 3. Track effective emotions (will be used in response generation)
        emotion = self._extract_emotion_from_response(feedback.response_text)
        if emotion:
            self.effective_emotions[emotion] += success_score * self.adaptation_rate
    
    def _extract_emotion_from_response(self, text: str) -> Optional[str]:
        """Simple emotion extraction from response text"""
        # Simple keyword-based emotion detection
        emotion_keywords = {
            "excited": ["amazing", "incredible", "fantastic", "love"],
            "skeptical": ["however", "but", "doubt", "questionable"],
            "thinking": ["consider", "analyze", "examine", "perhaps"],
            "confident": ["certainly", "definitely", "clearly", "obviously"]
        }
        
        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        return None
    
    def get_topic_preference_score(self, topic: str) -> float:
        """Get preference score for a topic (-1 to 1)"""
        success_count = self.successful_topics.get(topic, 0)
        failure_count = self.failed_topics.get(topic, 0)
        
        if success_count + failure_count == 0:
            return 0.0  # Neutral for unknown topics
        
        return (success_count - failure_count) / (success_count + failure_count)
    
    def get_preferred_emotion(self) -> str:
        """Get the most effective emotion for this character"""
        if not self.effective_emotions:
            return "neutral"
        
        return max(self.effective_emotions.items(), key=lambda x: x[1])[0]
    
    def get_adaptation_summary(self) -> Dict:
        """Get summary of current adaptations"""
        return {
            "sessions_learned_from": len(self.recent_feedback),
            "top_successful_topics": dict(sorted(self.successful_topics.items(), 
                                               key=lambda x: x[1], reverse=True)[:5]),
            "avoided_topics": dict(sorted(self.failed_topics.items(), 
                                        key=lambda x: x[1], reverse=True)[:3]),
            "optimal_response_length": round(self.optimal_response_length),
            "preferred_emotion": self.get_preferred_emotion(),
            "adaptation_rate": self.adaptation_rate
        }