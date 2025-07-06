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
    """Character's learned adaptive traits - ENHANCED FOR EMERGENT BEHAVIOR"""
    
    # Topic preferences based on success
    successful_topics: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    failed_topics: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    
    # PEER-SPECIFIC LEARNING
    peer_interaction_patterns: Dict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
    peer_agreement_history: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    peer_engagement_history: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    
    # TOPIC + PEER COMBINATIONS
    topic_peer_success: Dict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(float)))
    
    # Phrase/pattern effectiveness
    effective_phrases: List[str] = field(default_factory=list)
    ineffective_phrases: List[str] = field(default_factory=list)
    
    # Response style adaptations
    optimal_response_length: float = 100.0  # Character count
    effective_emotions: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    
    # EMERGENT BEHAVIORAL PREFERENCES
    behavioral_tendencies: Dict[str, float] = field(default_factory=lambda: defaultdict(lambda: 0.5))
    response_style_preferences: Dict[str, float] = field(default_factory=lambda: defaultdict(lambda: 0.5))
    
    # Interaction patterns with other characters
    successful_interactions: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    # Recent session feedback (rolling window)
    recent_feedback: deque = field(default_factory=lambda: deque(maxlen=20))
    
    # Learning rate (how fast to adapt)
    adaptation_rate: float = 0.1
    
    def add_session_feedback(self, feedback: SessionFeedback):
        """Feedback from a completed session"""
        self.recent_feedback.append(feedback)
        self._update_adaptive_traits(feedback)
    
    def add_peer_interaction_feedback(self, peer_character: str, engagement: float, agreement: float, topic: str):
        """Peer-specific interaction feedback"""
        
        # Update peer interaction patterns
        self.peer_agreement_history[peer_character].append(agreement)
        self.peer_engagement_history[peer_character].append(engagement)
        
        # Keep only recent history
        if len(self.peer_agreement_history[peer_character]) > 20:
            self.peer_agreement_history[peer_character] = self.peer_agreement_history[peer_character][-20:]
        if len(self.peer_engagement_history[peer_character]) > 20:
            self.peer_engagement_history[peer_character] = self.peer_engagement_history[peer_character][-20:]
        
        # Update average patterns
        avg_agreement = sum(self.peer_agreement_history[peer_character]) / len(self.peer_agreement_history[peer_character])
        avg_engagement = sum(self.peer_engagement_history[peer_character]) / len(self.peer_engagement_history[peer_character])
        
        self.peer_interaction_patterns[peer_character]["agreement"] = avg_agreement
        self.peer_interaction_patterns[peer_character]["engagement"] = avg_engagement
        
        # Update topic + peer success patterns
        combined_score = (engagement * 0.6) + (agreement * 0.4)
        topic_key = self._normalize_topic(topic)
        
        current_success = self.topic_peer_success[topic_key][peer_character]
        self.topic_peer_success[topic_key][peer_character] = (
            current_success * 0.8 + combined_score * 0.2  # Exponential moving average
        )
    
    def _update_adaptive_traits(self, feedback: SessionFeedback):
        """Update traits based on session feedback - ENHANCED"""
        
        success_score = feedback.response_quality_score
        
        # 1. Update topic preferences
        topic_key = self._normalize_topic(feedback.topic)
        
        if success_score > 0.6:  # Successful
            self.successful_topics[topic_key] += self.adaptation_rate
            # behavioral tendencies based on success
            self._reinforce_successful_behaviors(feedback, success_score)
        elif success_score < 0.4:  # Failed
            self.failed_topics[topic_key] += self.adaptation_rate
            # behavioral tendencies based on failure
            self._adjust_failed_behaviors(feedback, success_score)
        
        # 2. Update optimal response length
        if success_score > 0.6:
            current_length = len(feedback.response_text)
            self.optimal_response_length += (current_length - self.optimal_response_length) * self.adaptation_rate
        
        # 3. Track effective emotions
        emotion = self._extract_emotion_from_response(feedback.response_text)
        if emotion:
            self.effective_emotions[emotion] += success_score * self.adaptation_rate
        
        # 4. Update general behavioral tendencies
        if feedback.conversation_continued:
            self.behavioral_tendencies["engagement_effectiveness"] += 0.05
        else:
            self.behavioral_tendencies["engagement_effectiveness"] -= 0.02
        
        # Clamp behavioral tendencies between 0 and 1
        for key in self.behavioral_tendencies:
            self.behavioral_tendencies[key] = max(0.0, min(1.0, self.behavioral_tendencies[key]))
    
    def _reinforce_successful_behaviors(self, feedback: SessionFeedback, success_score: float):
        """Reinforce behaviors that led to success"""
        
        # Analyze what made this successful
        text_length = len(feedback.response_text)
        
        # Length preference learning
        if text_length > 150:
            self.response_style_preferences["prefers_long_responses"] += 0.1 * success_score
        elif text_length < 50:
            self.response_style_preferences["prefers_short_responses"] += 0.1 * success_score
        
        # Topic continuation vs shift learning
        if not feedback.topic_shift_caused:
            self.behavioral_tendencies["topic_focus"] += 0.05 * success_score
        else:
            self.behavioral_tendencies["topic_exploration"] += 0.05 * success_score
    
    def _adjust_failed_behaviors(self, feedback: SessionFeedback, success_score: float):
        """Adjust behaviors that led to failure"""
        
        # Reduce confidence in failed approaches
        failure_strength = (0.5 - success_score) * 2  # Convert to 0-1 failure scale
        
        text_length = len(feedback.response_text)
        if text_length > 150:
            self.response_style_preferences["prefers_long_responses"] -= 0.05 * failure_strength
        elif text_length < 50:
            self.response_style_preferences["prefers_short_responses"] -= 0.05 * failure_strength
    
    def _normalize_topic(self, topic: str) -> str:
        """Normalize topic for consistent storage"""
        return "_".join(topic.lower().split()[:3])  # First 3 words
    
    def _extract_emotion_from_response(self, text: str) -> Optional[str]:
        """Simple emotion extraction from response text"""
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
        topic_key = self._normalize_topic(topic)
        success_count = self.successful_topics.get(topic_key, 0)
        failure_count = self.failed_topics.get(topic_key, 0)
        
        if success_count + failure_count == 0:
            return 0.0  # Neutral for unknown topics
        
        return (success_count - failure_count) / (success_count + failure_count)
    
    def get_peer_interaction_preference(self, peer_character: str, topic: str = None) -> Dict[str, float]:
        """Get interaction preferences with specific peer"""
        
        result = {
            "agreement_tendency": 0.5,
            "engagement_tendency": 0.5,
            "topic_specific_success": 0.5
        }
        
        # General peer patterns
        if peer_character in self.peer_interaction_patterns:
            patterns = self.peer_interaction_patterns[peer_character]
            result["agreement_tendency"] = patterns.get("agreement", 0.5)
            result["engagement_tendency"] = patterns.get("engagement", 0.5)
        
        # Topic-specific patterns
        if topic:
            topic_key = self._normalize_topic(topic)
            if topic_key in self.topic_peer_success and peer_character in self.topic_peer_success[topic_key]:
                result["topic_specific_success"] = self.topic_peer_success[topic_key][peer_character]
        
        return result
    
    def get_preferred_emotion(self) -> str:
        """Get the most effective emotion for this character"""
        if not self.effective_emotions:
            return "neutral"
        
        return max(self.effective_emotions.items(), key=lambda x: x[1])[0]
    
    def get_emergent_personality_summary(self) -> Dict:
        """Get emergent personality characteristics"""
        
        personality_traits = {}
        
        # Analyze behavioral tendencies for personality traits
        for tendency, value in self.behavioral_tendencies.items():
            if abs(value - 0.5) > 0.1:  # Significant deviation from neutral
                if value > 0.6:
                    personality_traits[f"high_{tendency}"] = value
                elif value < 0.4:
                    personality_traits[f"low_{tendency}"] = value
        
        # Analyze response style preferences
        response_style = {}
        for style, value in self.response_style_preferences.items():
            if abs(value - 0.5) > 0.1:
                response_style[style] = value
        
        # Analyze peer relationship patterns
        peer_relationships = {}
        for peer, patterns in self.peer_interaction_patterns.items():
            relationship_type = "neutral"
            agreement = patterns.get("agreement", 0.5)
            engagement = patterns.get("engagement", 0.5)
            
            if agreement > 0.7 and engagement > 0.6:
                relationship_type = "collaborative"
            elif agreement < 0.3 and engagement > 0.6:
                relationship_type = "competitive"
            elif engagement < 0.4:
                relationship_type = "distant"
            
            peer_relationships[peer] = {
                "type": relationship_type,
                "agreement": agreement,
                "engagement": engagement
            }
        
        return {
            "personality_traits": personality_traits,
            "response_style": response_style,
            "peer_relationships": peer_relationships,
            "topic_expertise": dict(sorted(self.successful_topics.items(), key=lambda x: x[1], reverse=True)[:5]),
            "avoided_topics": dict(sorted(self.failed_topics.items(), key=lambda x: x[1], reverse=True)[:3])
        }
    
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
            "adaptation_rate": self.adaptation_rate,
            "behavioral_tendencies": dict(self.behavioral_tendencies),
            "peer_patterns_learned": len(self.peer_interaction_patterns),
            "topic_peer_combinations": sum(len(peers) for peers in self.topic_peer_success.values())
        }