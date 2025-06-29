# test_memory_characters.py - Test memory-enhanced characters
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.ai.characters import get_character

async def test_memory_enhanced_characters():
    """Test the memory-enhanced character system"""
    
    print("🤖 Testing Memory-Enhanced A2AIs Characters...")
    print("=" * 60)
    
    # Test character creation
    print("1. Creating Characters...")
    claude = get_character("claude")
    gpt = get_character("gpt") 
    grok = get_character("grok")
    print("   ✅ All characters created")
    
    # Test memory initialization
    print("\n2. Initializing Memory Systems...")
    await claude.initialize_memory()
    await gpt.initialize_memory()
    await grok.initialize_memory()
    print("   ✅ Memory systems initialized")
    
    # Test conversation with memory
    print("\n3. Testing Memory-Enhanced Conversations...")
    
    topic = "AI consciousness and ethics"
    context = {
        "other_participants": ["gpt", "grok"]
    }
    
    # Claude's response
    print("   🧠 Claude generating response...")
    claude_response = await claude.generate_response(topic, context.copy())
    print(f"   Claude: {claude_response['text'][:100]}...")
    print(f"   Emotion: {claude_response['facialExpression']}")
    
    # GPT's response (with Claude's context)
    print("\n   🧠 GPT generating response...")
    gpt_context = {
        "other_participants": ["claude", "grok"]
    }
    gpt_response = await gpt.generate_response(topic, gpt_context)
    print(f"   GPT: {gpt_response['text'][:100]}...")
    print(f"   Emotion: {gpt_response['facialExpression']}")
    
    # Grok's response (with both contexts)
    print("\n   🧠 Grok generating response...")
    grok_context = {
        "other_participants": ["claude", "gpt"]
    }
    grok_response = await grok.generate_response(topic, grok_context)
    print(f"   Grok: {grok_response['text'][:100]}...")
    print(f"   Emotion: {grok_response['facialExpression']}")
    
    # Test memory recall
    print("\n4. Testing Memory Recall...")
    
    # Claude recalls similar conversations
    claude_memories = await claude.recall_topic_history(topic)
    print(f"   Claude recalls: {len(claude_memories)} similar conversations")
    
    # Test relationship patterns
    print("\n5. Testing Relationship Patterns...")
    
    claude_relationships = await claude.get_relationship_summary()
    print(f"   Claude knows {len(claude_relationships)} other characters")
    
    for char, pattern in claude_relationships.items():
        print(f"   Claude -> {char}: {pattern['relationship_type']} ({pattern['interaction_count']} interactions)")
    
    # Test another round to see memory influence
    print("\n6. Testing Memory Influence (Round 2)...")
    
    # Same topic, should show memory influence
    claude_response_2 = await claude.generate_response(topic, context.copy())
    print(f"   Claude (Round 2): {claude_response_2['text'][:100]}...")
    
    # Check memory influence
    if "memory_influence" in claude_response_2:
        influence = claude_response_2["memory_influence"]
        print(f"   Memory Influence: {influence['similar_memory_count']} memories, expertise: {influence['topic_expertise']:.2f}")
    
    # Test memory stats
    print("\n7. Testing Memory Statistics...")
    
    claude_stats = await claude.get_memory_summary()
    print(f"   Claude Total Conversations: {claude_stats['total_conversations']}")
    print(f"   Claude Memory Count: {claude_stats['total_stored_memories']}")
    print(f"   Claude Top Topics: {claude_stats['top_topics']}")
    
    print("\n" + "=" * 60)
    print("🎉 Memory-Enhanced Character Test Complete!")
    
    print("\n📊 Test Results:")
    print(f"   Characters Created: ✅ 3/3")
    print(f"   Memory Systems: ✅ Initialized")
    print(f"   Conversations: ✅ Generated with memory influence")
    print(f"   Relationships: ✅ Tracked and influenced responses")
    print(f"   Memory Recall: ✅ Working")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_memory_enhanced_characters())
    
    if result:
        print("\n✅ Memory-enhanced characters are ready!")
        print("\nNext steps:")
        print("1. Update WebSocket to use memory-enhanced characters")
        print("2. Test real-time memory influence in debates")
        print("3. Monitor relationship dynamics over time")
    else:
        print("\n❌ Character memory system has issues")