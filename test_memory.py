# test_memory.py - Memory system test script

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.ai.memory import embedding_service, vector_store, CharacterMemoryManager

async def test_memory_system():
    """Test the complete memory system"""
    
    print("🧠 Testing A2AIs Memory System...")
    print("=" * 50)
    
    # 1. Test Embedding Service
    print("1. Testing Embedding Service...")
    embedding_test = await embedding_service.test_connection()
    print(f"   Embeddings: {'✅ Working' if embedding_test else '❌ Failed (using mock)'}")
    
    # 2. Test Vector Store
    print("2. Testing Vector Store...")
    vector_test = await vector_store.test_connection()
    print(f"   Qdrant: {'✅ Connected' if vector_test else '❌ Failed (using mock)'}")
    
    # 3. Test Character Memory Manager
    print("3. Testing Character Memory...")
    claude_memory = CharacterMemoryManager("claude")
    await claude_memory.initialize()
    
    # Store test conversation
    success = await claude_memory.store_conversation(
        text="I think AI consciousness is a fascinating topic that requires careful ethical consideration.",
        emotion="thinking",
        topic="AI consciousness",
        other_participants=["gpt", "grok"]
    )
    print(f"   Store Memory: {'✅ Success' if success else '❌ Failed'}")
    
    # Recall similar conversations
    memories = await claude_memory.recall_similar_conversations(
        current_topic="AI consciousness",
        current_context="discussing ethics"
    )
    print(f"   Recall Memory: ✅ Found {len(memories)} similar conversations")
    
    # Get relationship patterns
    gpt_relationship = await claude_memory.get_relationship_pattern("gpt")
    print(f"   Relationships: ✅ GPT interaction count: {gpt_relationship['interaction_count']}")
    
    # Get memory stats
    stats = await claude_memory.get_memory_stats()
    print(f"   Memory Stats: ✅ Total conversations: {stats['total_conversations']}")
    
    print("\n" + "=" * 50)
    print("🎉 Memory System Test Complete!")
    print("\nMemory Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return True

if __name__ == "__main__":
    # Test the memory system
    result = asyncio.run(test_memory_system())
    
    if result:
        print("\n✅ Memory system is ready!")
        print("\nNext steps:")
        print("1. Add memory to your character classes")
        print("2. Update WebSocket to use memory-enhanced characters")
        print("3. Test with real conversations")
    else:
        print("\n❌ Memory system has issues - check logs")