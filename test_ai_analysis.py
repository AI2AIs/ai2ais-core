# test_ai_analysis.py
import asyncio
from app.core.ai.characters.ai_response_analyzer import AIResponseAnalyzer

async def test_ai_analysis():
    # Claude analyzing GPT's response
    claude_analyzer = AIResponseAnalyzer("claude")
    
    gpt_response = "This is absolutely incredible! Imagine the revolutionary possibilities this could create!"
    
    claude_reaction = await claude_analyzer.analyze_response(
        other_character_id="gpt",
        response_text=gpt_response,
        response_emotion="excited", 
        topic="AI consciousness"
    )
    
    print("🔍 Claude analyzing GPT:")
    print(f"   Engagement: {claude_reaction.engagement_level}")
    print(f"   Agreement: {claude_reaction.agreement_level}")
    print(f"   Should respond: {claude_reaction.should_respond}")
    print(f"   Emotional response: {claude_reaction.emotional_response}")
    print(f"   Counter strategy: {claude_reaction.counter_strategy}")
    print(f"   Overall quality: {claude_reaction.get_overall_quality_score()}")

asyncio.run(test_ai_analysis())