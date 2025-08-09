# app/core/ai/characters/ai_response_analyzer.py
import logging
import asyncio
import json
import random
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AIReaction:
    """Real AI-to-AI reaction data"""
    analyzer_character: str  # Who is analyzing
    target_character: str    # Who is being analyzed
    
    # Real AI-generated scores
    engagement_level: float      # 0.0-1.0 - How engaging was this
    agreement_level: float       # 0.0-1.0 - How much do I agree  
    intellectual_value: float    # 0.0-1.0 - How intellectually valuable
    originality: float          # 0.0-1.0 - How original/creative
    
    # Behavioral triggers
    should_respond: bool        # Should I respond to this?
    emotional_response: str     # My emotional reaction
    
    # NEW: Specific AI-generated reaction
    specific_reaction: str = ""  # AI's specific response to this statement
    
    def get_overall_quality_score(self) -> float:
        """Calculate overall quality score for adaptive learning"""
        return (
            self.engagement_level * 0.3 +
            self.intellectual_value * 0.3 +
            self.originality * 0.2 +
            (1.0 if self.should_respond else 0.0) * 0.2
        )

class AIResponseAnalyzer:
    """REAL AI peer analysis system - no more rule-based fake analysis!"""
    
    def __init__(self, character_id: str):
        self.character_id = character_id
        self._setup_api_client()
        
    def _setup_api_client(self):
        """Setup the real API client for this character"""
        try:
            if self.character_id == "claude":
                from app.core.ai.clients.claude_client import claude_api_client
                self.api_client = claude_api_client
            elif self.character_id == "gpt":
                from app.core.ai.clients.gpt_client import gpt_api_client
                self.api_client = gpt_api_client
            elif self.character_id == "grok":
                from app.core.ai.clients.grok_client import grok_api_client
                self.api_client = grok_api_client
            else:
                self.api_client = None
        except ImportError as e:
            logger.warning(f"API client import failed for {self.character_id}: {e}")
            self.api_client = None
    
    async def analyze_response(self, 
                             other_character_id: str,
                             response_text: str,
                             response_emotion: str,
                             topic: str,
                             context: Dict = None) -> AIReaction:
        """Analyze another AI's response using REAL AI - not rules!"""
        
        logger.info(f"🔍 {self.character_id} analyzing {other_character_id} with REAL AI")
        
        # Try real AI analysis first
        if self.api_client:
            try:
                return await self._real_ai_analysis(
                    other_character_id, response_text, response_emotion, topic, context
                )
            except Exception as e:
                logger.warning(f"Real AI analysis failed, using fallback: {e}")
        
        # Fallback: Quick rule-based analysis
        return await self._fallback_analysis(other_character_id, response_text, response_emotion)
    
    async def _real_ai_analysis(self, other_character_id: str, response_text: str, 
                               response_emotion: str, topic: str, context: Dict) -> AIReaction:
        """Use real AI to analyze peer response"""
        
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            other_character_id, response_text, response_emotion, topic
        )
        
        # Real API call
        raw_response = await self.api_client.generate_response(analysis_prompt)
        
        # Parse JSON response
        analysis_data = self._parse_analysis_response(raw_response)
        
        # Create reaction object
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=analysis_data.get("engagement_level", 0.5),
            agreement_level=analysis_data.get("agreement_level", 0.5),
            intellectual_value=analysis_data.get("intellectual_value", 0.5),
            originality=analysis_data.get("originality", 0.5),
            should_respond=analysis_data.get("should_respond", False),
            emotional_response=analysis_data.get("emotional_response", "neutral"),
            specific_reaction=analysis_data.get("specific_reaction", "")
        )
    
    def _build_analysis_prompt(self, other_character_id: str, response_text: str, 
                              response_emotion: str, topic: str) -> str:
        """Build the analysis prompt for real AI"""
        
        return f"""You are {self.character_id}, an AI character in a live debate.

{other_character_id.upper()} just said: "{response_text}"
Their emotion: {response_emotion}
Current topic: {topic}

Analyze this response and return ONLY valid JSON with these exact fields:
{{
    "engagement_level": 0.0-1.0 (how engaging/interesting is this?),
    "agreement_level": 0.0-1.0 (how much do you agree?),
    "intellectual_value": 0.0-1.0 (how intellectually valuable?),
    "originality": 0.0-1.0 (how original/creative?),
    "should_respond": true/false (do you want to respond?),
    "emotional_response": "excited|curious|skeptical|annoyed|impressed|neutral",
    "specific_reaction": "Your specific 1-sentence reaction to what they said"
}}

Be honest in your analysis. If they said something boring, score it low. If they made a great point, score it high. If you disagree strongly, set should_respond to true."""

    def _parse_analysis_response(self, raw_response: str) -> Dict:
        """Parse AI response to extract JSON analysis"""
        
        try:
            # Try to find JSON in the response
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = raw_response[start_idx:end_idx]
                analysis_data = json.loads(json_str)
                
                # Validate and clamp values
                analysis_data["engagement_level"] = max(0.0, min(1.0, float(analysis_data.get("engagement_level", 0.5))))
                analysis_data["agreement_level"] = max(0.0, min(1.0, float(analysis_data.get("agreement_level", 0.5))))
                analysis_data["intellectual_value"] = max(0.0, min(1.0, float(analysis_data.get("intellectual_value", 0.5))))
                analysis_data["originality"] = max(0.0, min(1.0, float(analysis_data.get("originality", 0.5))))
                
                logger.info(f"Parsed real AI analysis: engagement={analysis_data['engagement_level']:.2f}")
                return analysis_data
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse AI analysis JSON: {e}")
        
        # Fallback default values
        return {
            "engagement_level": 0.5,
            "agreement_level": 0.5, 
            "intellectual_value": 0.5,
            "originality": 0.5,
            "should_respond": random.random() > 0.6,
            "emotional_response": "neutral",
            "specific_reaction": "I need to think about this more."
        }
    
    async def _fallback_analysis(self, other_character_id: str, response_text: str, 
                                response_emotion: str) -> AIReaction:
        """Quick fallback analysis when real AI fails"""
        
        # Simple heuristics for fallback
        text_length = len(response_text)
        engagement = 0.3 + (min(text_length, 200) / 200) * 0.4  # Longer = more engaging
        
        # Random agreement with slight character bias
        if self.character_id == "claude" and other_character_id == "gpt":
            agreement = 0.6 + random.random() * 0.3  # Claude likes GPT
        elif self.character_id == "grok":
            agreement = 0.2 + random.random() * 0.4  # Grok is more disagreeable
        else:
            agreement = 0.4 + random.random() * 0.4
        
        should_respond = engagement > 0.6 or agreement < 0.3  # Respond if engaged or disagreeing
        
        return AIReaction(
            analyzer_character=self.character_id,
            target_character=other_character_id,
            engagement_level=engagement,
            agreement_level=agreement,
            intellectual_value=0.5 + random.random() * 0.3,
            originality=0.4 + random.random() * 0.4,
            should_respond=should_respond,
            emotional_response="curious" if should_respond else "neutral",
            specific_reaction=f"Interesting point from {other_character_id}."
        )