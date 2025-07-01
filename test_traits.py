import asyncio
from app.core.ai.characters import get_character

async def main():
    claude = get_character("claude")

    claude.start_session("test-adaptive-001")

    # Response
    response = await claude.generate_response(
        topic="AI consciousness",
        context={"other_participants": ["gpt", "grok"]}
    )

    print("Response:", response["text"][:100])
    print("Adaptive metadata:", response.get("adaptive_metadata"))

    await claude.end_session_with_feedback(
        session_id="test-adaptive-001",
        other_participants=["gpt", "grok"],
        topic="AI consciousness", 
        response_text=response["text"],
        quality_score=0.8  # Good response
    )

    # Adaptive summary'i gör
    summary = await claude.get_adaptive_summary()
    print("Evolution stage:", summary["character_evolution"]["evolution_stage"])

if __name__ == "__main__":
    asyncio.run(main())