# test_peer_feedback.py
import asyncio
from app.core.ai.characters import get_character

async def test_peer_feedback_system():
    print("🧠 Testing AI-to-AI Peer Feedback System...")
    
    # Create characters
    claude = get_character("claude")
    gpt = get_character("gpt")
    
    # Initialize
    await claude.initialize_memory()
    await gpt.initialize_memory()
    
    # Start session for Claude
    claude.start_session("peer-feedback-test-001")
    
    # Simulate GPT's response
    gpt_response = "This is absolutely incredible! Imagine the revolutionary possibilities!"
    gpt_emotion = "excited"
    topic = "AI consciousness"
    
    # Claude analyzes GPT's response
    claude_reaction = await claude.analyze_peer_response(
        peer_character_id="gpt",
        peer_response_text=gpt_response,
        peer_emotion=gpt_emotion,
        topic=topic
    )
    
    print(f"🔍 Claude's analysis of GPT:")
    print(f"   Engagement: {claude_reaction.engagement_level}")
    print(f"   Should respond: {claude_reaction.should_respond}")
    print(f"   Overall quality: {claude_reaction.get_overall_quality_score()}")
    
    # Simulate Claude receiving peer feedback
    await claude.receive_peer_feedback([claude_reaction])
    
    # Calculate peer feedback score
    peer_score = claude.calculate_peer_feedback_score()
    print(f"📊 Claude's peer feedback score: {peer_score}")
    
    # Generate response with peer context
    response = await claude.generate_response(topic, {
        "other_participants": ["gpt", "grok"]
    })
    
    print(f"💬 Claude's response with peer influence:")
    print(f"   Text: {response['text'][:100]}...")
    print(f"   Emotion: {response['facialExpression']}")
    
    # End session with peer feedback
    await claude.end_session_with_feedback(
        session_id="peer-feedback-test-001",
        other_participants=["gpt", "grok"],
        topic=topic,
        response_text=response["text"]
    )
    
    # Get peer feedback summary
    summary = await claude.get_peer_feedback_summary()
    print(f"📈 Peer feedback summary: {summary}")

asyncio.run(test_peer_feedback_system())