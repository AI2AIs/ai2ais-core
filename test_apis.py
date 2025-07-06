"""
A2AIs Real API Peer Analysis Test
Test if peer analysis uses real APIs or local logic
"""

import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_peer_analysis():
    """Test if peer analysis actually uses real APIs"""
    
    print("🔬 A2AIs Real Peer Analysis Test")
    print("Testing if AI characters use real APIs to analyze each other")
    print("=" * 70)
    
    # Import characters
    from app.core.ai.characters.claude import ClaudeCharacter
    from app.core.ai.characters.gpt import GPTCharacter
    from app.core.ai.characters.grok import GrokCharacter
    
    # Create characters
    claude = ClaudeCharacter()
    gpt = GPTCharacter() 
    grok = GrokCharacter()
    
    # Initialize memory
    print("🧠 Initializing character memories...")
    await claude.initialize_memory()
    await gpt.initialize_memory()
    await grok.initialize_memory()
    
    print("✅ Memory initialized for all characters\n")
    
    # Step 1: Generate real responses
    print("📝 Step 1: Generate Real API Responses")
    print("-" * 40)
    
    topic = "Should AI have consciousness?"
    
    # Claude's real response
    print("🤖 Claude generating response...")
    claude_response = await claude.generate_response(topic)
    claude_text = claude_response["text"]
    claude_emotion = claude_response["facialExpression"]
    
    print(f"💭 Claude: {claude_text[:100]}...")
    print(f"😊 Claude Emotion: {claude_emotion}")
    
    # GPT's real response  
    print("\n🤖 GPT generating response...")
    gpt_response = await gpt.generate_response(topic)
    gpt_text = gpt_response["text"]
    gpt_emotion = gpt_response["facialExpression"]
    
    print(f"💭 GPT: {gpt_text[:100]}...")
    print(f"😊 GPT Emotion: {gpt_emotion}")
    
    # Step 2: Test peer analysis
    print(f"\n🔍 Step 2: Peer Analysis Test")
    print("-" * 40)
    
    # Test 1: Does Claude analyze GPT using real API?
    print("\n🔬 Test 1: Claude analyzing GPT's response...")
    print(f"   📝 Analyzing: \"{gpt_text[:80]}...\"")
    
    start_time = time.time()
    
    try:
        # This should call analyze_peer_response
        claude_reaction = await claude.analyze_peer_response(
            peer_character_id="gpt",
            peer_response_text=gpt_text,
            peer_emotion=gpt_emotion,
            topic=topic,
            context={"test_mode": True}
        )
        
        analysis_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️  Analysis Time: {analysis_time:.0f}ms")
        print(f"   📊 Engagement Level: {claude_reaction.engagement_level:.3f}")
        print(f"   🤝 Agreement Level: {claude_reaction.agreement_level:.3f}")
        print(f"   🎯 Should Respond: {claude_reaction.should_respond}")
        print(f"   😮 Emotional Response: {claude_reaction.emotional_response}")
        print(f"   🔍 Analysis Method: {claude_reaction.discovery_method if hasattr(claude_reaction, 'discovery_method') else 'Unknown'}")
        
        # KEY TEST: Is this real API analysis?
        if analysis_time > 500:  # Real API calls take time
            print("   ✅ LIKELY REAL API: Analysis took substantial time")
        else:
            print("   ⚠️  LIKELY LOCAL LOGIC: Analysis was very fast")
            
    except Exception as e:
        print(f"   ❌ Analysis Failed: {e}")
    
    # Test 2: Does GPT analyze Claude using real API?
    print("\n🔬 Test 2: GPT analyzing Claude's response...")
    print(f"   📝 Analyzing: \"{claude_text[:80]}...\"")
    
    start_time = time.time()
    
    try:
        gpt_reaction = await gpt.analyze_peer_response(
            peer_character_id="claude",
            peer_response_text=claude_text,
            peer_emotion=claude_emotion,
            topic=topic,
            context={"test_mode": True}
        )
        
        analysis_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️  Analysis Time: {analysis_time:.0f}ms")
        print(f"   📊 Engagement Level: {gpt_reaction.engagement_level:.3f}")
        print(f"   🤝 Agreement Level: {gpt_reaction.agreement_level:.3f}")
        print(f"   🎯 Should Respond: {gpt_reaction.should_respond}")
        print(f"   😮 Emotional Response: {gpt_reaction.emotional_response}")
        
        if analysis_time > 500:
            print("   ✅ LIKELY REAL API: Analysis took substantial time")
        else:
            print("   ⚠️  LIKELY LOCAL LOGIC: Analysis was very fast")
            
    except Exception as e:
        print(f"   ❌ Analysis Failed: {e}")
    
    # Test 3: Does Grok analyze both using real API?
    print("\n🔬 Test 3: Grok analyzing both responses...")
    
    # Grok analyzes Claude
    start_time = time.time()
    try:
        grok_reaction_claude = await grok.analyze_peer_response(
            peer_character_id="claude",
            peer_response_text=claude_text,
            peer_emotion=claude_emotion,
            topic=topic
        )
        
        analysis_time_1 = (time.time() - start_time) * 1000
        print(f"   📊 Grok → Claude: Engagement {grok_reaction_claude.engagement_level:.3f}, Time {analysis_time_1:.0f}ms")
        
    except Exception as e:
        print(f"   ❌ Grok → Claude failed: {e}")
        analysis_time_1 = 0
    
    # Grok analyzes GPT
    start_time = time.time()
    try:
        grok_reaction_gpt = await grok.analyze_peer_response(
            peer_character_id="gpt",
            peer_response_text=gpt_text,
            peer_emotion=gpt_emotion,
            topic=topic
        )
        
        analysis_time_2 = (time.time() - start_time) * 1000
        print(f"   📊 Grok → GPT: Engagement {grok_reaction_gpt.engagement_level:.3f}, Time {analysis_time_2:.0f}ms")
        
    except Exception as e:
        print(f"   ❌ Grok → GPT failed: {e}")
        analysis_time_2 = 0
    
    # Step 3: Analysis Summary
    print(f"\n📋 Step 3: Analysis Summary")
    print("-" * 40)
    
    total_analyses = 0
    real_api_analyses = 0
    local_logic_analyses = 0
    
    analysis_times = [t for t in [analysis_time, analysis_time_1, analysis_time_2] if t > 0]
    
    for t in analysis_times:
        total_analyses += 1
        if t > 500:
            real_api_analyses += 1
        else:
            local_logic_analyses += 1
    
    print(f"   📊 Total Peer Analyses: {total_analyses}")
    print(f"   🌐 Likely Real API: {real_api_analyses}")
    print(f"   💻 Likely Local Logic: {local_logic_analyses}")
    
    if analysis_times:
        avg_time = sum(analysis_times) / len(analysis_times)
        print(f"   ⏱️  Average Analysis Time: {avg_time:.0f}ms")
    
    # Final verdict
    print(f"\n🎯 VERDICT:")
    if real_api_analyses > local_logic_analyses:
        print("   ✅ PEER ANALYSIS USES REAL APIs")
        print("   🔥 AI characters are actually analyzing each other with API calls!")
    elif local_logic_analyses > real_api_analyses:
        print("   ⚠️  PEER ANALYSIS USES LOCAL LOGIC")
        print("   💡 AI characters use rule-based analysis, not real API calls")
    else:
        print("   🤔 INCONCLUSIVE RESULTS")
        print("   📝 Need more testing to determine analysis method")
    
    # Step 4: Test peer-triggered responses
    print(f"\n💬 Step 4: Peer-Triggered Response Test")
    print("-" * 40)
    
    # Send Claude the GPT reaction and see if it responds
    if 'claude_reaction' in locals() and claude_reaction.should_respond:
        print("🎤 Claude received peer feedback and should respond...")
        
        try:
            # Send peer feedback
            await claude.receive_peer_feedback([claude_reaction])
            
            # Generate follow-up response
            start_time = time.time()
            follow_up = await claude.generate_response(
                topic=f"Responding to GPT about {topic}",
                context={
                    "peer_triggered": True,
                    "responding_to": ["gpt"],
                    "other_participants": ["gpt", "grok"]
                }
            )
            
            response_time = (time.time() - start_time) * 1000
            
            print(f"   💬 Follow-up Response ({response_time:.0f}ms):")
            print(f"   📝 Text: {follow_up['text'][:150]}...")
            print(f"   😊 Emotion: {follow_up['facialExpression']}")
            
            if response_time > 1000:
                print("   ✅ REAL API: Follow-up response used real API")
            else:
                print("   ⚠️  TEMPLATE: Follow-up response was templated")
                
        except Exception as e:
            print(f"   ❌ Follow-up response failed: {e}")
    else:
        print("   😐 Claude chose not to respond (or analysis failed)")
    
    print(f"\n🎉 Real Peer Analysis Test Complete!")

async def main():
    """Run the test"""
    await test_real_peer_analysis()

if __name__ == "__main__":
    asyncio.run(main())