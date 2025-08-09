# app/core/content/autonomous_topic_selector.py
import asyncio
import logging
import random
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.core.ai.characters import get_character
from app.core.content.topic_sources import TopicDetector, TopicSource

logger = logging.getLogger(__name__)

@dataclass
class AITopicAnalysis:
    character_id: str
    topic: TopicSource
    interest_level: float      # 0-1, how interested this AI is
    debate_potential: float    # 0-1, how much debate this could generate
    personal_angle: str        # What angle this AI would take
    expected_emotion: str      # What emotion they'd have
    confidence: float          # 0-1, how confident they are about this topic

class AutonomousTopicSelector:
    """Let AI characters autonomously choose and evaluate topics"""
    
    def __init__(self):
        self.topic_detector = TopicDetector()
        self.characters = {}
        self.topic_history = []  # Track what topics were already used
        
    async def initialize_characters(self):
        """Initialize AI characters for topic selection"""
        for char_id in ["claude", "gpt", "grok"]:
            self.characters[char_id] = get_character(char_id)
            await self.characters[char_id].initialize_memory()
        
        logger.info("🤖 AI characters initialized for autonomous topic selection")

    async def ai_select_topic(self, candidate_topics: List[TopicSource] = None) -> Dict:
        """Let AI characters autonomously select the best topic"""
        
        logger.info("Starting AI autonomous topic selection...")
        
        # 1. Get candidate topics if not provided
        if not candidate_topics:
            candidate_topics = await self.topic_detector.get_trending_topics(count=10, force_refresh=True)
        
        # Filter out recently used topics
        fresh_topics = self._filter_recent_topics(candidate_topics)
        
        if len(fresh_topics) < 3:
            logger.warning("⚠️ Not enough fresh topics, using some recent ones")
            fresh_topics = candidate_topics[:5]
        
        logger.info(f"valuating {len(fresh_topics)} candidate topics with AI characters")
        
        # 2. Each AI character analyzes each topic
        ai_analyses = {}
        
        for char_id in ["claude", "gpt", "grok"]:
            logger.info(f"{char_id} analyzing topics...")
            char_analyses = await self._ai_analyze_topics(char_id, fresh_topics[:5])
            ai_analyses[char_id] = char_analyses
        
        # 3. AI characters vote/discuss which topic to choose
        selected_topic_data = await self._ai_consensus_selection(ai_analyses, fresh_topics[:5])
        
        # 4. Store in history to avoid repetition
        self.topic_history.append({
            "topic": selected_topic_data["topic"],
            "timestamp": time.time(),
            "selected_by": selected_topic_data["primary_selector"],
            "consensus_score": selected_topic_data["consensus_score"]
        })
        
        logger.info(f"AI selected topic: {selected_topic_data['topic'].title[:50]}...")
        
        return selected_topic_data

    async def _ai_analyze_topics(self, character_id: str, topics: List[TopicSource]) -> List[AITopicAnalysis]:
        """Have a specific AI character analyze topics"""
        
        character = self.characters[character_id]
        analyses = []
        
        for topic in topics:
            try:
                # Generate AI's analysis of this topic
                analysis_prompt = f"""
                Topic: "{topic.title}"
                Source: {topic.source}
                Keywords: {', '.join(topic.keywords[:5])}
                
                Analyze this topic from your perspective as {character_id}:
                1. How interested are you in this topic? (0-1)
                2. How much debate potential does it have? (0-1)  
                3. What angle would you take in discussing this?
                4. What emotion would you feel about this topic?
                5. How confident are you about this subject? (0-1)
                
                Respond as {character_id} would respond.
                """
                
                # Generate character's response
                response = await character.generate_response(
                    topic=analysis_prompt,
                    context={
                        "analysis_mode": True,
                        "topic_evaluation": True,
                        "character_perspective": character_id
                    }
                )
                
                # Parse AI's response to extract metrics
                analysis = self._parse_ai_topic_analysis(
                    character_id, topic, response["text"], response["facialExpression"]
                )
                
                analyses.append(analysis)
                
                logger.debug(f"   {character_id} topic analysis: interest={analysis.interest_level:.2f}, debate={analysis.debate_potential:.2f}")
                
            except Exception as e:
                logger.error(f"{character_id} failed to analyze topic '{topic.title}': {e}")
                
                # Fallback analysis
                fallback_analysis = self._generate_fallback_analysis(character_id, topic)
                analyses.append(fallback_analysis)
        
        return analyses

    def _parse_ai_topic_analysis(self, character_id: str, topic: TopicSource, 
                                ai_response: str, ai_emotion: str) -> AITopicAnalysis:
        """Parse AI's natural language response into structured analysis"""
        
        response_lower = ai_response.lower()
        
        # Extract interest level from AI's language
        interest_level = 0.5  # default
        
        # High interest indicators
        if any(word in response_lower for word in ["fascinating", "incredibly", "really interested", "love this", "excited"]):
            interest_level = 0.8 + random.random() * 0.2
        elif any(word in response_lower for word in ["interesting", "intriguing", "curious", "compelling"]):
            interest_level = 0.6 + random.random() * 0.3
        elif any(word in response_lower for word in ["boring", "uninteresting", "not relevant", "don't care"]):
            interest_level = 0.1 + random.random() * 0.3
        
        # Extract debate potential from AI's analysis
        debate_potential = 0.5  # default
        
        if any(phrase in response_lower for phrase in ["highly controversial", "debate potential", "strongly disagree", "contentious"]):
            debate_potential = 0.8 + random.random() * 0.2
        elif any(word in response_lower for word in ["controversial", "disagreement", "debate", "argue"]):
            debate_potential = 0.6 + random.random() * 0.3
        elif any(word in response_lower for word in ["consensus", "everyone agrees", "obvious", "settled"]):
            debate_potential = 0.2 + random.random() * 0.3
        
        # Extract personal angle from response
        personal_angle = self._extract_personal_angle(character_id, ai_response)
        
        # Extract confidence level
        confidence = 0.5  # default
        
        if any(word in response_lower for word in ["confident", "certain", "definitely", "clearly"]):
            confidence = 0.7 + random.random() * 0.3
        elif any(word in response_lower for word in ["uncertain", "maybe", "not sure", "unclear"]):
            confidence = 0.2 + random.random() * 0.4
        
        # Character-specific adjustments
        if character_id == "claude":
            # Claude tends to be more measured
            interest_level *= 0.9
            confidence *= 0.8
        elif character_id == "gpt":
            # GPT tends to be more enthusiastic
            interest_level *= 1.1
            debate_potential *= 1.1
        elif character_id == "grok":
            # Grok is more selective but confident
            if interest_level > 0.6:
                interest_level *= 1.2
            confidence *= 1.1
        
        return AITopicAnalysis(
            character_id=character_id,
            topic=topic,
            interest_level=min(1.0, interest_level),
            debate_potential=min(1.0, debate_potential),
            personal_angle=personal_angle,
            expected_emotion=ai_emotion,
            confidence=min(1.0, confidence)
        )

    def _extract_personal_angle(self, character_id: str, ai_response: str) -> str:
        """Extract what angle the AI would take on this topic"""
        
        response_lower = ai_response.lower()
        
        # Character-specific angle detection
        if character_id == "claude":
            if "ethical" in response_lower or "implications" in response_lower:
                return "ethical_implications"
            elif "careful" in response_lower or "cautious" in response_lower:
                return "cautious_analysis"
            else:
                return "thoughtful_examination"
        
        elif character_id == "gpt":
            if "creative" in response_lower or "possibilities" in response_lower:
                return "creative_exploration"
            elif "exciting" in response_lower or "innovative" in response_lower:
                return "optimistic_expansion"
            else:
                return "enthusiastic_support"
        
        elif character_id == "grok":
            if "problem" in response_lower or "issues" in response_lower:
                return "problem_identification"
            elif "realistic" in response_lower or "practical" in response_lower:
                return "reality_check"
            else:
                return "skeptical_analysis"
        
        return "general_interest"

    def _generate_fallback_analysis(self, character_id: str, topic: TopicSource) -> AITopicAnalysis:
        """Generate fallback analysis if AI response fails"""
        
        # Character-specific default preferences
        base_preferences = {
            "claude": {
                "interest_base": 0.6,
                "debate_base": 0.7,
                "angle": "ethical_considerations",
                "emotion": "thinking"
            },
            "gpt": {
                "interest_base": 0.8,
                "debate_base": 0.6,
                "angle": "creative_possibilities", 
                "emotion": "excited"
            },
            "grok": {
                "interest_base": 0.5,
                "debate_base": 0.8,
                "angle": "realistic_concerns",
                "emotion": "skeptical"
            }
        }
        
        prefs = base_preferences.get(character_id, base_preferences["claude"])
        
        # Adjust based on topic characteristics
        interest_adjustment = topic.ai_relevance * 0.3
        debate_adjustment = topic.controversy_score * 0.2
        
        return AITopicAnalysis(
            character_id=character_id,
            topic=topic,
            interest_level=min(1.0, prefs["interest_base"] + interest_adjustment),
            debate_potential=min(1.0, prefs["debate_base"] + debate_adjustment),
            personal_angle=prefs["angle"],
            expected_emotion=prefs["emotion"],
            confidence=0.6 + random.random() * 0.3
        )

    async def _ai_consensus_selection(self, ai_analyses: Dict[str, List[AITopicAnalysis]], 
                                    topics: List[TopicSource]) -> Dict:
        """Let AI characters reach consensus on topic selection"""
        
        logger.info("🗳️ AI characters voting on best topic...")
        
        # Calculate combined scores for each topic
        topic_scores = {}
        
        for topic in topics:
            scores = []
            character_votes = {}
            
            for char_id, analyses in ai_analyses.items():
                # Find this character's analysis of this topic
                char_analysis = next(
                    (a for a in analyses if a.topic.title == topic.title), 
                    None
                )
                
                if char_analysis:
                    # Calculate this character's vote score
                    vote_score = (
                        char_analysis.interest_level * 0.4 +
                        char_analysis.debate_potential * 0.4 +
                        char_analysis.confidence * 0.2
                    )
                    
                    scores.append(vote_score)
                    character_votes[char_id] = {
                        "score": vote_score,
                        "analysis": char_analysis
                    }
            
            if scores:
                # Weighted average (some characters might have more influence)
                weights = {"claude": 1.0, "gpt": 1.0, "grok": 1.1}  # Grok slightly more weight for controversy
                
                weighted_score = sum(
                    score * weights.get(char_id, 1.0) 
                    for char_id, vote_data in character_votes.items()
                    for score in [vote_data["score"]]
                ) / sum(weights.get(char_id, 1.0) for char_id in character_votes.keys())
                
                topic_scores[topic.title] = {
                    "topic": topic,
                    "consensus_score": weighted_score,
                    "character_votes": character_votes,
                    "vote_spread": max(scores) - min(scores) if len(scores) > 1 else 0
                }
        
        # Select topic with highest consensus score
        if not topic_scores:
            logger.error("No topics received any votes!")
            return None
        
        best_topic_data = max(topic_scores.values(), key=lambda x: x["consensus_score"])
        
        # Determine primary selector (character who was most enthusiastic)
        primary_selector = max(
            best_topic_data["character_votes"].items(),
            key=lambda x: x[1]["score"]
        )[0]
        
        # Log the AI decision process
        logger.info(f"  AI Consensus Results:")
        logger.info(f"   Selected Topic: {best_topic_data['topic'].title}")
        logger.info(f"   Consensus Score: {best_topic_data['consensus_score']:.3f}")
        logger.info(f"   Primary Selector: {primary_selector}")
        logger.info(f"   Vote Spread: {best_topic_data['vote_spread']:.3f}")
        
        for char_id, vote_data in best_topic_data["character_votes"].items():
            analysis = vote_data["analysis"]
            logger.info(f"   {char_id}: {vote_data['score']:.3f} (interest={analysis.interest_level:.2f}, debate={analysis.debate_potential:.2f})")
        
        return {
            "topic": best_topic_data["topic"],
            "consensus_score": best_topic_data["consensus_score"],
            "primary_selector": primary_selector,
            "character_votes": best_topic_data["character_votes"],
            "ai_decision_rationale": f"{primary_selector} led selection with {best_topic_data['character_votes'][primary_selector]['analysis'].personal_angle}"
        }

    def _filter_recent_topics(self, topics: List[TopicSource]) -> List[TopicSource]:
        """Filter out topics that were recently used"""
        
        if not self.topic_history:
            return topics
        
        # Get titles of recently used topics (last 10)
        recent_titles = {
            entry["topic"].title.lower().strip() 
            for entry in self.topic_history[-10:]
        }
        
        # Filter out similar topics
        fresh_topics = []
        for topic in topics:
            topic_title = topic.title.lower().strip()
            
            # Check for exact matches or very similar topics
            is_recent = any(
                topic_title == recent_title or 
                self._topics_similar(topic_title, recent_title)
                for recent_title in recent_titles
            )
            
            if not is_recent:
                fresh_topics.append(topic)
        
        logger.info(f"🔄 Filtered {len(topics) - len(fresh_topics)} recent topics")
        return fresh_topics

    def _topics_similar(self, title1: str, title2: str) -> bool:
        """Check if two topics are too similar"""
        
        # Simple similarity check based on common words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        # If they share more than 50% of words, consider them similar
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = words1.intersection(words2)
        similarity = len(intersection) / min(len(words1), len(words2))
        
        return similarity > 0.5

    async def get_ai_selected_topic(self) -> Optional[Dict]:
        """Main method: Let AI autonomously select a topic"""
        
        try:
            if not self.characters:
                await self.initialize_characters()
            
            # Let AI characters autonomously select topic
            selected_topic_data = await self.ai_select_topic()
            
            if selected_topic_data:
                logger.info(f"  AI autonomous topic selection completed!")
                logger.info(f"   Topic: {selected_topic_data['topic'].title}")
                logger.info(f"   Selected by: {selected_topic_data['primary_selector']}")
                logger.info(f"   Rationale: {selected_topic_data['ai_decision_rationale']}")
            
            return selected_topic_data
            
        except Exception as e:
            logger.error(f"AI topic selection failed: {e}")
            import traceback
            traceback.print_exc()
            return None

# Global instance
autonomous_topic_selector = AutonomousTopicSelector()