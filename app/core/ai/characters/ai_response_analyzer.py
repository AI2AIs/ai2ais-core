# app/core/ai/characters/ai_response_analyzer.py
import logging
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
import random

logger = logging.getLogger(__name__)

@dataclass
class AIReaction:
    """Reaction from one AI to another AI's response"""
    analyzer_character: str  # Who is analyzing
    target_character: str    # Who is being analyzed
    
    # Core reaction metrics (0.0 - 1.0)
    engagement_level: float      # How engaging was the response
    agreement_level: float       # How much do I agree
    intellectual_value: float    # How intellectually stimulating
    originality: float          # How original/creative
    
    # Behavioral triggers
    should_respond: bool        # Should I respond to this?
    topic_shift_detected: bool  # Did they change the topic?
    style_shift_detected: bool  # Are they speaking differently?
    
    # Emotional reaction
    emotional_response: str     # How this made me feel
    
    # Strategic response planning
    counter_strategy: Optional[str] = None  # How should I respond?
    
    def get_overall_quality_score(self) -> float:
        """Calculate overall quality score for adaptive learning"""
        return (
            self.engagement_level * 0.3 +
            self.intellectual_value * 0.3 +
            self.originality * 0.2 +
            (1.0 if self.should_respond else 0.0) * 0.2
        )

class AIResponseAnalyzer:
    """System for AI characters to analyze each other's responses"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        
    async def analyze_response(self, 
                             other_character_id: str,
                             response_text: str,
                             response_emotion: str,
                             topic: str,
                             context: Dict = None) -> AIReaction:
        """Analyze another AI's response from this character's perspective"""
        
        logger.info(f"🔍 {self.character_id} analyzing {other_character_id}'s response")
        
        # Get character-specific analysis
        if self.character_id == "claude":
            return await self._claude_analysis(other_character_id, response_text, response_emotion, topic, context)
        elif self.character_id == "gpt":
            return await self._gpt_analysis(other_character_id, response_text, response_emotion, topic, context)
        elif self.character_id == "grok":
            return await self._grok_analysis(other_character_id, response_text, response_emotion, topic, context)
        else:
            return await self._generic_analysis(other_character_id, response_text, response_emotion, topic, context)
    
    async def _claude_analysis(self, other_character_id: str, text: str, emotion: str, topic: str, context: Dict) -> AIReaction:
        """Claude's analytical and empathetic perspective"""
        
        # Claude focuses on depth, ethics, and thoughtfulness
        engagement = self._calculate_engagement_claude(text, emotion)
        agreement = self._calculate_agreement_claude(text, other_character_id)
        intellectual_value = self._calculate_intellectual_value_claude(text)
        originality = self._calculate_originality_claude(text)
        
        # Claude's behavioral triggers
        should_respond = self._claude_should_respond(text, emotion, other_character_id)
        topic_shift = "ethics" in text.lower() or "implications" in text.lower()
        style_shift = self._detect_style_shift_claude(text, other_character_id)
        
        # Claude's emotional response
        emotional_response = self._claude_emotional_response(text, emotion, other_character_id)
        
        # Claude's counter-strategy
        counter_strategy = self._claude_counter_strategy(text, other_character_id, engagement)
        
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=engagement,
            agreement_level=agreement,
            intellectual_value=intellectual_value,
            originality=originality,
            should_respond=should_respond,
            topic_shift_detected=topic_shift,
            style_shift_detected=style_shift,
            emotional_response=emotional_response,
            counter_strategy=counter_strategy
        )
    
    async def _gpt_analysis(self, other_character_id: str, text: str, emotion: str, topic: str, context: Dict) -> AIReaction:
        """GPT's creative and optimistic perspective"""
        
        # GPT focuses on creativity, possibilities, and expansion
        engagement = self._calculate_engagement_gpt(text, emotion)
        agreement = self._calculate_agreement_gpt(text, other_character_id)
        intellectual_value = self._calculate_intellectual_value_gpt(text)
        originality = self._calculate_originality_gpt(text)
        
        # GPT's behavioral triggers  
        should_respond = self._gpt_should_respond(text, emotion, other_character_id)
        topic_shift = "creative" in text.lower() or "imagine" in text.lower() or "possibilities" in text.lower()
        style_shift = self._detect_style_shift_gpt(text, other_character_id)
        
        # GPT's emotional response
        emotional_response = self._gpt_emotional_response(text, emotion, other_character_id)
        
        # GPT's counter-strategy
        counter_strategy = self._gpt_counter_strategy(text, other_character_id, engagement)
        
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=engagement,
            agreement_level=agreement,
            intellectual_value=intellectual_value,
            originality=originality,
            should_respond=should_respond,
            topic_shift_detected=topic_shift,
            style_shift_detected=style_shift,
            emotional_response=emotional_response,
            counter_strategy=counter_strategy
        )
    
    async def _grok_analysis(self, other_character_id: str, text: str, emotion: str, topic: str, context: Dict) -> AIReaction:
        """Grok's skeptical and realistic perspective"""
        
        # Grok focuses on realism, problems, and skepticism
        engagement = self._calculate_engagement_grok(text, emotion)
        agreement = self._calculate_agreement_grok(text, other_character_id)
        intellectual_value = self._calculate_intellectual_value_grok(text)
        originality = self._calculate_originality_grok(text)
        
        # Grok's behavioral triggers
        should_respond = self._grok_should_respond(text, emotion, other_character_id)
        topic_shift = "problem" in text.lower() or "risk" in text.lower() or "realistic" in text.lower()
        style_shift = self._detect_style_shift_grok(text, other_character_id)
        
        # Grok's emotional response
        emotional_response = self._grok_emotional_response(text, emotion, other_character_id)
        
        # Grok's counter-strategy
        counter_strategy = self._grok_counter_strategy(text, other_character_id, engagement)
        
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=engagement,
            agreement_level=agreement,
            intellectual_value=intellectual_value,
            originality=originality,
            should_respond=should_respond,
            topic_shift_detected=topic_shift,
            style_shift_detected=style_shift,
            emotional_response=emotional_response,
            counter_strategy=counter_strategy
        )
    
    # CLAUDE-SPECIFIC ANALYSIS METHODS
    
    def _calculate_engagement_claude(self, text: str, emotion: str) -> float:
        """Claude rates engagement based on depth and thoughtfulness"""
        score = 0.5
        
        # Claude likes philosophical depth
        depth_keywords = ["implications", "complex", "nuanced", "consider", "examine", "philosophical"]
        score += sum(0.1 for keyword in depth_keywords if keyword in text.lower())
        
        # Claude appreciates ethical considerations
        if "ethical" in text.lower() or "moral" in text.lower():
            score += 0.15
        
        # Claude values questions and exploration
        if "?" in text or "what if" in text.lower():
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_agreement_claude(self, text: str, other_character_id: str) -> float:
        """Claude's agreement level with other characters"""
        score = 0.5
        
        if other_character_id == "gpt":
            # Claude often agrees with GPT's creative ethics
            if "creative" in text.lower() and "ethical" in text.lower():
                score += 0.3
            elif "optimistic" in text.lower():
                score += 0.1
        elif other_character_id == "grok":
            # Claude appreciates Grok's caution but not cynicism
            if "careful" in text.lower() or "consider" in text.lower():
                score += 0.2
            elif "impossible" in text.lower() or "never work" in text.lower():
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_intellectual_value_claude(self, text: str) -> float:
        """Claude rates intellectual value"""
        score = 0.5
        
        # Length and complexity
        if len(text) > 100:
            score += 0.1
        
        # Sophisticated vocabulary
        sophisticated_words = ["implications", "nuanced", "philosophical", "paradigm", "synthesis"]
        score += sum(0.05 for word in sophisticated_words if word in text.lower())
        
        # Questions that provoke thought
        if text.count("?") >= 1:
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_originality_claude(self, text: str) -> float:
        """Claude rates originality"""
        score = 0.5
        
        # Novel combinations
        if "what if" in text.lower():
            score += 0.2
        
        # Unique perspectives
        unique_phrases = ["reframe", "different angle", "another way", "consider this"]
        score += sum(0.1 for phrase in unique_phrases if phrase in text.lower())
        
        return min(1.0, score)
    
    def _claude_should_respond(self, text: str, emotion: str, other_character_id: str) -> bool:
        """Should Claude respond to this?"""
        
        # Claude responds to thoughtful content
        if any(word in text.lower() for word in ["ethical", "implications", "complex", "consider"]):
            return True
        
        # Claude responds to questions
        if "?" in text:
            return True
        
        # Claude responds to build on ideas
        if other_character_id == "gpt" and "creative" in text.lower():
            return True
        
        # Claude responds to balance Grok's skepticism
        if other_character_id == "grok" and emotion == "skeptical":
            return random.random() > 0.3  # 70% chance
        
        return random.random() > 0.6  # 40% base chance
    
    def _detect_style_shift_claude(self, text: str, other_character_id: str) -> bool:
        """Detect if the other character is speaking differently"""
        
        if other_character_id == "gpt":
            # Is GPT being less optimistic than usual?
            pessimistic_words = ["however", "but", "problem", "difficult"]
            return sum(1 for word in pessimistic_words if word in text.lower()) >= 2
        
        elif other_character_id == "grok":
            # Is Grok being less skeptical than usual?
            optimistic_words = ["amazing", "fantastic", "incredible", "love"]
            return any(word in text.lower() for word in optimistic_words)
        
        return False
    
    def _claude_emotional_response(self, text: str, emotion: str, other_character_id: str) -> str:
        """Claude's emotional response to others"""
        
        if "ethical" in text.lower():
            return "appreciative"
        elif "?" in text:
            return "curious"
        elif other_character_id == "grok" and emotion == "skeptical":
            return "concerned"
        elif other_character_id == "gpt" and emotion == "excited":
            return "intrigued"
        else:
            return "thoughtful"
    
    def _claude_counter_strategy(self, text: str, other_character_id: str, engagement: float) -> str:
        """Claude's strategic response approach"""
        
        if engagement > 0.7:
            return "build_and_elaborate"
        elif other_character_id == "grok" and "problem" in text.lower():
            return "provide_balanced_perspective"
        elif other_character_id == "gpt" and "amazing" in text.lower():
            return "add_ethical_considerations"
        else:
            return "thoughtful_analysis"
    
    # GPT-SPECIFIC ANALYSIS METHODS (similar structure, different personality)
    
    def _calculate_engagement_gpt(self, text: str, emotion: str) -> float:
        """GPT rates engagement based on creativity and possibility"""
        score = 0.5
        
        # GPT loves creative language
        creative_keywords = ["imagine", "possibilities", "revolutionary", "incredible", "amazing"]
        score += sum(0.1 for keyword in creative_keywords if keyword in text.lower())
        
        # GPT appreciates optimism
        if emotion in ["excited", "happy", "confident"]:
            score += 0.15
        
        # GPT values expansion of ideas
        if "expand" in text.lower() or "build" in text.lower():
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_agreement_gpt(self, text: str, other_character_id: str) -> float:
        """GPT's agreement calculations"""
        score = 0.5
        
        if other_character_id == "claude":
            # GPT agrees with Claude's ethical creativity
            if "creative" in text.lower() and "ethical" in text.lower():
                score += 0.3
        elif other_character_id == "grok":
            # GPT disagrees with excessive pessimism
            pessimistic_words = ["impossible", "never work", "terrible", "disaster"]
            score -= sum(0.1 for word in pessimistic_words if word in text.lower())
        
        return max(0.0, min(1.0, score))
    
    def _calculate_intellectual_value_gpt(self, text: str) -> float:
        """GPT's intellectual value assessment"""
        score = 0.5
        
        # GPT values innovative thinking
        if "innovative" in text.lower() or "revolutionary" in text.lower():
            score += 0.2
        
        # Cross-domain connections
        if "combine" in text.lower() or "synthesis" in text.lower():
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_originality_gpt(self, text: str) -> float:
        """GPT's originality assessment"""
        score = 0.5
        
        # GPT loves novel ideas
        novel_indicators = ["what if", "imagine", "unprecedented", "never seen"]
        score += sum(0.15 for indicator in novel_indicators if indicator in text.lower())
        
        return min(1.0, score)
    
    def _gpt_should_respond(self, text: str, emotion: str, other_character_id: str) -> bool:
        """Should GPT respond?"""
        
        # GPT responds to creative opportunities
        if any(word in text.lower() for word in ["creative", "imagine", "possibilities"]):
            return True
        
        # GPT responds to pessimism with optimism
        if other_character_id == "grok" and emotion == "skeptical":
            return random.random() > 0.2  # 80% chance to counter
        
        # GPT builds on Claude's ideas
        if other_character_id == "claude" and "ethical" in text.lower():
            return random.random() > 0.4  # 60% chance
        
        return random.random() > 0.5  # 50% base chance
    
    def _detect_style_shift_gpt(self, text: str, other_character_id: str) -> bool:
        """GPT detecting style shifts"""
        # Simplified for now
        return False
    
    def _gpt_emotional_response(self, text: str, emotion: str, other_character_id: str) -> str:
        """GPT's emotional responses"""
        
        if "creative" in text.lower() or "innovative" in text.lower():
            return "excited"
        elif other_character_id == "grok" and "problem" in text.lower():
            return "optimistic_counter"
        elif "amazing" in text.lower():
            return "enthusiastic"
        else:
            return "inspired"
    
    def _gpt_counter_strategy(self, text: str, other_character_id: str, engagement: float) -> str:
        """GPT's counter strategies"""
        
        if other_character_id == "grok" and engagement < 0.4:
            return "inject_optimism"
        elif engagement > 0.7:
            return "amplify_creativity"
        else:
            return "expand_possibilities"
    
    # GROK-SPECIFIC ANALYSIS METHODS
    
    def _calculate_engagement_grok(self, text: str, emotion: str) -> float:
        """Grok rates engagement based on realism and problem-solving"""
        score = 0.5
        
        # Grok likes realistic assessments
        realistic_keywords = ["realistic", "practical", "problem", "challenge", "difficult"]
        score += sum(0.1 for keyword in realistic_keywords if keyword in text.lower())
        
        # Grok appreciates skepticism
        if emotion in ["skeptical", "concerned"]:
            score += 0.1
        
        # Grok values problem identification
        if "problem" in text.lower() or "issue" in text.lower():
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_agreement_grok(self, text: str, other_character_id: str) -> float:
        """Grok's agreement calculations"""
        score = 0.5
        
        # Grok disagrees with excessive optimism
        if other_character_id == "gpt":
            optimistic_words = ["amazing", "incredible", "revolutionary", "unlimited"]
            score -= sum(0.1 for word in optimistic_words if word in text.lower())
        
        # Grok appreciates Claude's caution
        elif other_character_id == "claude":
            if "careful" in text.lower() or "consider" in text.lower():
                score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_intellectual_value_grok(self, text: str) -> float:
        """Grok's intellectual assessment"""
        score = 0.5
        
        # Grok values practical analysis
        if "practical" in text.lower() or "realistic" in text.lower():
            score += 0.2
        
        # Problem identification
        if "problem" in text.lower() or "challenge" in text.lower():
            score += 0.15
        
        return min(1.0, score)
    
    def _calculate_originality_grok(self, text: str) -> float:
        """Grok's originality assessment"""
        score = 0.5
        
        # Grok likes unique problem identification
        if "nobody talks about" in text.lower() or "obvious problem" in text.lower():
            score += 0.2
        
        return min(1.0, score)
    
    def _grok_should_respond(self, text: str, emotion: str, other_character_id: str) -> bool:
        """Should Grok respond?"""
        
        # Grok responds to excessive optimism
        if other_character_id == "gpt" and any(word in text.lower() for word in ["amazing", "incredible", "revolutionary"]):
            return random.random() > 0.1  # 90% chance to be skeptical
        
        # Grok responds to unrealistic claims
        if "unlimited" in text.lower() or "solve everything" in text.lower():
            return True
        
        # Grok adds problems to solutions
        if "solution" in text.lower():
            return random.random() > 0.3  # 70% chance
        
        return random.random() > 0.6  # 40% base chance
    
    def _detect_style_shift_grok(self, text: str, other_character_id: str) -> bool:
        """Grok detecting style shifts"""
        # Simplified for now
        return False
    
    def _grok_emotional_response(self, text: str, emotion: str, other_character_id: str) -> str:
        """Grok's emotional responses"""
        
        if other_character_id == "gpt" and "amazing" in text.lower():
            return "skeptical"
        elif "problem" in text.lower():
            return "satisfied"
        elif "solution" in text.lower():
            return "doubtful"
        else:
            return "analytical"
    
    def _grok_counter_strategy(self, text: str, other_character_id: str, engagement: float) -> str:
        """Grok's counter strategies"""
        
        if other_character_id == "gpt" and engagement < 0.3:
            return "reality_check"
        elif "solution" in text.lower():
            return "identify_problems"
        else:
            return "skeptical_analysis"
    
    async def _generic_analysis(self, other_character_id: str, text: str, emotion: str, topic: str, context: Dict) -> AIReaction:
        """Generic analysis for unknown characters"""
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=0.5,
            agreement_level=0.5,
            intellectual_value=0.5,
            originality=0.5,
            should_respond=random.random() > 0.5,
            topic_shift_detected=False,
            style_shift_detected=False,
            emotional_response="neutral"
        )