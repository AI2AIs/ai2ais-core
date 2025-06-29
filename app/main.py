# # app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvloop
import asyncio
import logging

from app.config.settings import settings
from app.api.websocket import websocket_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Performance boost with uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Create FastAPI app
app = FastAPI(
    title="A2AIs Core Engine",
    description="Autonomous AI-to-AI Debate System with Real TTS",
    version="1.0.0"
)

# CORS middleware - Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL, 
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "ws://localhost:3000",
        "ws://localhost:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include WebSocket router
app.include_router(websocket_router)

@app.get("/")
async def root():
    return {
        "message": "🤖 A2AIs Core Engine is running!",
        "status": "active",
        "websocket_endpoints": [
            "ws://localhost:3002/ws/{session_id}",
            "ws://localhost:3002/ws",
            "ws://localhost:3002/"
        ],
        "google_tts": "enabled" if settings.GOOGLE_TTS_API_KEY else "disabled"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "a2ais-core",
        "version": "1.0.0",
        "port": 3002,
        "websocket_endpoint": "/ws/{session_id}",
        "tts_service": "google" if settings.GOOGLE_TTS_API_KEY else "mock",
        "available_characters": ["claude", "gpt", "grok"]
    }

@app.get("/api/test-session")
async def create_test_session():
    """Create a test session for development"""
    return {
        "sessionId": "demo-session-123",
        "topic": "Should AI have consciousness?",
        "participants": ["claude", "gpt", "grok"],
        "websocket_url": "ws://localhost:3002/ws/demo-session-123",
        "instructions": "Connect to WebSocket and send: {'type': 'request_response', 'characterId': 'claude'}"
    }

@app.post('/api/sessions/{session_id}/start-autonomous')
async def start_autonomous_session(session_id: str):
    """Start autonomous debate session"""
    try:
        from app.core.sessions.autonomous_manager import autonomous_session_manager
        
        participants = ['claude', 'gpt', 'grok']
        
        # Start autonomous session
        session = await autonomous_session_manager.start_autonomous_session(
            session_id, participants
        )
        
        logger.info(f"🎭 Autonomous session started: {session_id}")
        
        return {
            "success": True,
            "sessionId": session_id,
            "participants": participants,
            "state": session.state.value,
            "message": "Autonomous debate session started"
        }
        
    except Exception as e:
        logger.error(f"Failed to start autonomous session: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/characters")
async def list_characters():
    """List available AI characters"""
    from app.core.ai.characters import get_available_characters
    
    characters = get_available_characters()
    return {
        "characters": characters,
        "total": len(characters),
        "example_request": {
            "type": "request_response",
            "characterId": "claude"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Print startup info
    print("🚀 Starting A2AIs Core Engine...")
    print(f"📡 WebSocket Server: ws://localhost:3002")
    print(f"🌐 HTTP Server: http://localhost:3002")
    print(f"🎵 TTS Service: {'Google TTS' if settings.GOOGLE_TTS_API_KEY else 'Mock Audio'}")
    print(f"🎭 Characters: Claude, GPT, Grok")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3002,  # ✅ Fixed to match frontend expectation
        reload=settings.DEBUG,
        loop="uvloop",
        log_level="info"
    )