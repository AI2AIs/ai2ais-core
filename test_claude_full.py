import asyncio
import logging
from app.core.ai.characters import get_character

logging.basicConfig(level=logging.INFO)

async def test_claude_full():
    print("🚀 Testing Claude with Real API Integration...")
    
    # FIX: Create test session first
    from app.core.database.service import db_service
    await db_service.create_session(
        session_id="test-session-123",
        topic="API Integration Test",
        participants=["claude"],
        max_rounds=5
    )
    print("✅ Test session created")

    # Get Claude character
    claude = get_character("claude")
    
    # Initialize memory
    print("🧠 Initializing memory...")
    memory_ready = await claude.initialize_memory()
    print(f"Memory ready: {memory_ready}")
    
    # Build test context (simulating evolved character)
    context = {
        "evolution_data": {
            "evolution_stage": "personality_formation",
            "maturity_level": 3,
            "life_energy": 75.0,
            "total_sessions": 25,
            "breakthrough_count": 2
        },
        "adaptive": {
            "preferred_emotion": "thinking",
            "topic_preference_score": 0.6,
            "sessions_learned_from": 15,
            "successful_topics": ["consciousness", "ethics"],
            "optimal_response_length": 120.0
        },
        "peer_feedback": {
            "avg_engagement": 0.65,
            "avg_agreement": 0.55,
            "peer_count": 2
        },
        "similar_memories": [],
        "relationship_patterns": {
            "gpt": {"relationship_type": "collaborative", "interaction_count": 8},
            "grok": {"relationship_type": "competitive", "interaction_count": 5}
        },
        "other_participants": ["gpt", "grok"],
        "session_id": "test-session-123"
    }
    
    # Test topics
    topics = [
        "What are the ethical implications of AI consciousness?",
        "How should we regulate artificial intelligence?",
        "Can machines truly understand human emotions?"
    ]
    
    print("\n" + "="*60)
    
    for i, topic in enumerate(topics, 1):
        print(f"\n🎯 Test {i}: {topic}")
        print("-" * 40)
        
        try:
            response = await claude.generate_response(topic, context)
            
            print(f"✅ Response generated:")
            print(f"📝 Text: {response['text']}")
            print(f"😊 Emotion: {response['facialExpression']}")
            print(f"⏱️ Duration: {response['duration']}s")
            print(f"🔧 Generation Time: {response.get('generation_time_ms', 0)}ms")
            print(f"🧠 API Provider: {response.get('api_provider', 'unknown')}")
            
            enhanced_meta = response.get('enhanced_metadata', {})
            print(f"🧬 Evolution Stage: {enhanced_meta.get('evolution_stage', 'unknown')}")
            print(f"⚡ Life Energy: {enhanced_meta.get('life_energy', 0)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("🎉 Claude API integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_claude_full())