# app/api/websocket.py 

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import logging
import time
import os

from app.core.ai.characters import get_character

# Logger setup
logger = logging.getLogger(__name__)

# WebSocket router
websocket_router = APIRouter()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sessions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(websocket)
        
        logger.info(f"✅ Client connected to session: {session_id}")

    async def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.sessions and websocket in self.sessions[session_id]:
            self.sessions[session_id].remove(websocket)
            if not self.sessions[session_id]:
                del self.sessions[session_id]
        
        logger.info(f"❌ Client disconnected from session: {session_id}")

    async def send_to_session(self, session_id: str, message: dict):
        """Send message to all clients in a session"""
        if session_id in self.sessions:
            dead_connections = []
            for connection in self.sessions[session_id]:
                try:
                    await connection.send_json(message)
                    logger.info(f"📤 Sent {message['type']} to session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    dead_connections.append(connection)
            
            for connection in dead_connections:
                await self.disconnect(connection, session_id)

# Global connection manager
manager = ConnectionManager()

# AI Response Storage for peer feedback
class AIResponseTracker:
    def __init__(self):
        self.session_responses: Dict[str, List[Dict]] = {}
        self.character_instances: Dict[str, object] = {}
    
    def get_or_create_character(self, character_id: str):
        """Get or create character instance"""
        if character_id not in self.character_instances:
            self.character_instances[character_id] = get_character(character_id)
        return self.character_instances[character_id]
    
    def add_response(self, session_id: str, character_id: str, response_data: Dict):
        """Add a response to session tracking"""
        if session_id not in self.session_responses:
            self.session_responses[session_id] = []
        
        self.session_responses[session_id].append({
            "character_id": character_id,
            "response_data": response_data,
            "timestamp": time.time()
        })
        
        logger.info(f"📝 Tracked response from {character_id} in session {session_id}")
    
    async def process_peer_feedback(self, session_id: str, new_response: Dict):
        """Process peer feedback for all characters"""
        
        if session_id not in self.session_responses:
            return
        
        recent_responses = self.session_responses[session_id][-5:]  # Last 5 responses
        new_character_id = new_response["character_id"]
        
        # Get all other characters who need to analyze this response
        other_characters = [r["character_id"] for r in recent_responses 
                          if r["character_id"] != new_character_id]
        
        peer_reactions = []
        
        for other_character_id in set(other_characters):  # Remove duplicates
            try:
                character = self.get_or_create_character(other_character_id)
                await character.initialize_memory()
                
                # Each character analyzes the new response
                reaction = await character.analyze_peer_response(
                    peer_character_id=new_character_id,
                    peer_response_text=new_response["response_data"]["text"],
                    peer_emotion=new_response["response_data"]["facialExpression"],
                    topic="artificial consciousness and the future of AI",  # Current topic
                    context={"session_id": session_id}
                )
                
                peer_reactions.append(reaction)
                
                logger.info(f"🔍 {other_character_id} analyzed {new_character_id}: "
                           f"engagement={reaction.engagement_level:.2f}, "
                           f"should_respond={reaction.should_respond}")
                
            except Exception as e:
                logger.error(f"❌ Failed peer analysis {other_character_id} -> {new_character_id}: {e}")
        
        # Send peer feedback to the character who just responded
        if peer_reactions:
            try:
                character = self.get_or_create_character(new_character_id)
                await character.receive_peer_feedback(peer_reactions)
                
                # Trigger follow-up responses based on peer reactions
                await self.trigger_follow_up_responses(session_id, peer_reactions)
                
            except Exception as e:
                logger.error(f"❌ Failed to process peer feedback for {new_character_id}: {e}")
    
    async def trigger_follow_up_responses(self, session_id: str, peer_reactions: List):
        """Trigger follow-up responses from characters who want to respond"""
        
        for reaction in peer_reactions:
            if reaction.should_respond and reaction.engagement_level > 0.6:
                # This character wants to respond with high engagement
                responding_character_id = reaction.analyzer_character
                
                logger.info(f"🎤 Triggering follow-up response from {responding_character_id}")
                
                # Trigger response generation in background
                asyncio.create_task(
                    generate_ai_response(session_id, responding_character_id, peer_triggered=True)
                )
                
                # Add delay to prevent simultaneous responses
                await asyncio.sleep(2.0)

# Global response tracker
response_tracker = AIResponseTracker()

# Main AI response generation with full peer feedback
async def generate_ai_response(session_id: str, character_id: str, peer_triggered: bool = False):
    """Generate AI response with FULL AI-to-AI feedback system"""

    request_key = f"{session_id}:{character_id}"
    if request_key in active_requests:
        logger.info(f"🚫 Duplicate request ignored for {character_id}")
        return
    
    active_requests.add(request_key)

    try:
        trigger_type = "peer-triggered" if peer_triggered else "manual"
        logger.info(f"🤖 Generating ADAPTIVE response for {character_id} ({trigger_type})")
        
        # Get character instance
        character = response_tracker.get_or_create_character(character_id)
        await character.initialize_memory()
        
        # Start session tracking for adaptive learning
        character.start_session(session_id)
        
        topic = "artificial consciousness and the future of AI"
        
        # Enhanced context with other participants for relationship tracking
        other_participants = [
            cid for cid in ["claude", "gpt", "grok"] 
            if cid != character_id
        ]
        
        context = {
            "other_participants": other_participants,
            "session_id": session_id,
            "session_type": "autonomous_debate",
            "peer_triggered": peer_triggered
        }
        
        # Generate character response with adaptive + peer feedback
        response_data = await character.generate_response(topic, context)
        
        print(f"💬 {character_id} ({trigger_type}): {response_data['text'][:100]}...")
        print(f"🎯 Adaptive: {response_data.get('adaptive_metadata', {})}")
        
        # TTS + Lip-sync generation
        try:
            from app.core.media.tts.google_tts import tts_service
            from app.core.media.tts.lip_sync import lip_sync_generator
            
            # Generate TTS
            tts_result = await tts_service.generate_speech_with_file(
                text=response_data["text"],
                character_id=character_id,
                emotion=response_data.get("facialExpression", "neutral")
            )
            
            if tts_result["success"] and "audioFilePath" in tts_result:
                lip_sync_result = await lip_sync_generator.generate_lip_sync_from_audio(
                    audio_file_path=tts_result["audioFilePath"],
                    text=response_data["text"]
                )
                tts_service.cleanup_temp_file(tts_result["audioFilePath"])
                final_duration = tts_result.get("duration", response_data.get("duration", 3.0))
                final_audio_base64 = tts_result["audioBase64"]
            else:
                # Fallback
                tts_result_fallback = await tts_service.generate_speech(
                    text=response_data["text"],
                    character_id=character_id,
                    emotion=response_data.get("facialExpression", "neutral")
                )
                
                lip_sync_result = await lip_sync_generator.generate_lip_sync(
                    text=response_data["text"],
                    duration=tts_result_fallback.get("duration", 3.0)
                )
                
                final_duration = tts_result_fallback.get("duration", 3.0)
                final_audio_base64 = tts_result_fallback["audioBase64"]
                
        except Exception as tts_error:
            logger.error(f"❌ TTS/Lip-sync failed for {character_id}: {tts_error}")
            final_duration = response_data.get("duration", 3.0)
            final_audio_base64 = "mock_audio_fallback"
            lip_sync_result = {
                "metadata": {"duration": final_duration}, 
                "mouthCues": [{"start": 0.0, "end": final_duration, "value": "A"}]
            }
        
        # Enhanced message with AI-to-AI feedback metadata
        complete_message = {
            "id": str(uuid.uuid4()),
            "sessionId": session_id,
            "characterId": character_id,
            "text": response_data["text"],
            "facialExpression": response_data.get("facialExpression", "neutral"),
            "animation": "Talking_1",
            "duration": final_duration,
            "timestamp": int(time.time() * 1000),
            
            # Audio/TTS fields
            "audioBase64": final_audio_base64,
            "lipSync": lip_sync_result,
            "audioUrl": None,
            
            # AI-to-AI feedback metadata
            "adaptiveMetadata": response_data.get("adaptive_metadata", {}),
            "aiToAiMetadata": {
                "triggerType": trigger_type,
                "peerTriggered": peer_triggered,
                "evolutionStage": character._determine_evolution_stage(),
                "sessionsCompleted": len(character.adaptive_traits.recent_feedback),
                "peerFeedbackScore": character.calculate_peer_feedback_score() if character._pending_peer_reactions else None
            },
            
            # Existing fields
            "personality_influence": response_data.get("personality_influence", {}),
            "energy_level": response_data.get("energy_level", 100.0),
            "resetExpressionAfter": True,
        }

        # Add to response tracking for peer feedback
        response_tracker.add_response(session_id, character_id, complete_message)
        
        # Process peer feedback asynchronously
        asyncio.create_task(
            response_tracker.process_peer_feedback(session_id, {
                "character_id": character_id,
                "response_data": complete_message
            })
        )
        
        # End session with peer feedback (will use peer scores automatically)
        await character.end_session_with_feedback(
            session_id=session_id,
            other_participants=other_participants,
            topic=topic,
            response_text=response_data["text"]
        )
        
        # Register with autonomous session manager
        try:
            from app.core.sessions.autonomous_manager import autonomous_session_manager
            session = autonomous_session_manager.get_session(session_id)
            if session:
                session.register_speech_start(
                    character_id=character_id,
                    text=response_data["text"],
                    duration=final_duration
                )
        except Exception as session_error:
            logger.debug(f"No autonomous session found: {session_error}")
        
        # Print AI-to-AI ecosystem status
        print(f"🧠 AI-TO-AI ECOSYSTEM STATUS:")
        print(f"   Character: {complete_message['characterId']}")
        print(f"   Trigger: {trigger_type}")
        print(f"   Evolution: {complete_message['aiToAiMetadata']['evolutionStage']}")
        print(f"   Peer Score: {complete_message['aiToAiMetadata']['peerFeedbackScore']}")
        
        # Send response message
        response_message = {
            "type": "new_message",
            "sessionId": session_id,
            "data": {
                "message": complete_message 
            },
            "timestamp": int(time.time() * 1000)
        }
        
        await manager.send_to_session(session_id, response_message)
        
        logger.info(f"✅ Complete AI-to-AI response sent for {character_id}")
        print(f"🚀 {character_id} finished speaking in AI ecosystem!")
        
    except Exception as e:
        logger.error(f"❌ AI response generation error for {character_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error message
        error_message = {
            "type": "error",
            "sessionId": session_id,
            "data": {
                "error": f"Failed to generate response for {character_id}: {str(e)}"
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            await manager.send_to_session(session_id, error_message)
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
    
    finally:
        active_requests.discard(request_key)

# Character-specific rate limiting (keep existing)
last_request_time = {}
active_requests = set()

# WebSocket message handling with AI-to-AI triggers
async def handle_websocket_message(websocket: WebSocket, session_id: str, data: dict):
    """Handle incoming WebSocket messages with AI-to-AI functionality"""
    message_type = data.get("type")
    
    if message_type == "join_session":
        await websocket.send_json({
            "type": "session_update",
            "sessionId": session_id,
            "data": {"message": "✅ Joined AI-to-AI ecosystem session"},
            "timestamp": time.time()
        })
    
    elif message_type == "request_response":
        character_id = (
            data.get("characterId") or 
            data.get("data", {}).get("characterId") or 
            "claude"
        )
        
        # Rate limiting check
        now = time.time()
        last_time = last_request_time.get(character_id, 0)

        if now - last_time < 1.0:
            logger.info(f"🕐 Rate limited request for {character_id}")
            return
        
        last_request_time[character_id] = now

        # Create background task for AI response with peer feedback
        asyncio.create_task(
            generate_ai_response(session_id, character_id, peer_triggered=False)
        )
    
    elif message_type == "get_ai_ecosystem_status":
        # Get AI-to-AI ecosystem status
        try:
            ecosystem_status = {}
            for character_id in ["claude", "gpt", "grok"]:
                character = response_tracker.get_or_create_character(character_id)
                await character.initialize_memory()
                
                peer_summary = await character.get_peer_feedback_summary()
                adaptive_summary = character.adaptive_traits.get_adaptation_summary()
                
                ecosystem_status[character_id] = {
                    "evolution_stage": character._determine_evolution_stage(),
                    "sessions_completed": len(character.adaptive_traits.recent_feedback),
                    "peer_feedback": peer_summary,
                    "adaptive_learning": adaptive_summary
                }
            
            await websocket.send_json({
                "type": "ai_ecosystem_status",
                "sessionId": session_id,
                "data": ecosystem_status,
                "timestamp": time.time()
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": f"Failed to get ecosystem status: {str(e)}",
                "timestamp": time.time()
            })
    
    elif message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": time.time()
        })
    
    else:
        logger.warning(f"❓ Unknown message type: {message_type}")

@websocket_router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    # Send welcome message with AI-to-AI info
    await websocket.send_json({
        "type": "session_update",
        "data": {"message": f"🤖 Connected to AI-to-AI Ecosystem: {session_id}"},
        "timestamp": time.time()
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"📨 Received: {data}")
            
            await handle_websocket_message(websocket, session_id, data)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await manager.disconnect(websocket, session_id)

@websocket_router.websocket("/ws")
async def websocket_root(websocket: WebSocket):
    """Root WebSocket endpoint"""
    await websocket_endpoint(websocket, "ai-ecosystem-demo")

@websocket_router.websocket("/")
async def websocket_root_alternative(websocket: WebSocket):
    """Alternative root WebSocket endpoint"""
    await websocket_endpoint(websocket, "ai-ecosystem-demo")