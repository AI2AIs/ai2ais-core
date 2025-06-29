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
        print(f"🔗 Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.sessions and websocket in self.sessions[session_id]:
            self.sessions[session_id].remove(websocket)
            if not self.sessions[session_id]:  # If session is empty
                del self.sessions[session_id]
        
        logger.info(f"❌ Client disconnected from session: {session_id}")
        print(f"🔗 Total connections: {len(self.active_connections)}")

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
            
            # Clean up dead connections
            for connection in dead_connections:
                await self.disconnect(connection, session_id)

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast failed: {e}")
                dead_connections.append(connection)
        
        # Clean up dead connections
        for connection in dead_connections:
            if connection in self.active_connections:
                self.active_connections.remove(connection)

# Global connection manager
manager = ConnectionManager()

@websocket_router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    # Send welcome message
    await websocket.send_json({
        "type": "session_update",
        "data": {"message": f"🎉 Connected to A2AIs session: {session_id}"},
        "timestamp": time.time()
    })
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            logger.info(f"📨 Received message: {data}")
            
            # Handle different message types
            await handle_websocket_message(websocket, session_id, data)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": time.time()
            })
        except:
            pass  # Connection might be closed

# Root WebSocket endpoints
@websocket_router.websocket("/ws")
async def websocket_root(websocket: WebSocket):
    """Root WebSocket endpoint for frontend compatibility"""
    await websocket_endpoint(websocket, "demo-session-123")

@websocket_router.websocket("/")
async def websocket_root_alternative(websocket: WebSocket):
    """Alternative root WebSocket endpoint"""
    await websocket_endpoint(websocket, "demo-session-123")

# Character-specific rate limiting
last_request_time = {}

async def handle_websocket_message(websocket: WebSocket, session_id: str, data: dict):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "join_session":
        # Session join confirmation
        await websocket.send_json({
            "type": "session_update",
            "sessionId": session_id,
            "data": {"message": "✅ Successfully joined session"},
            "timestamp": time.time()
        })
    
    elif message_type == "request_response":
        # AI response generation request
        character_id = (
            data.get("characterId") or 
            data.get("data", {}).get("characterId") or 
            "claude"  # Default fallback
        )
        
        # Rate limiting check
        now = time.time()
        last_time = last_request_time.get(character_id, 0)

        if now - last_time < 1.0:  # 1 second cooldown
            logger.info(f"🕐 Rate limited request for {character_id}")
            return
        
        last_request_time[character_id] = now

        # Create a background task for AI response
        asyncio.create_task(
            generate_ai_response(session_id, character_id)
        )
    
    elif message_type == "ping":
        # Health check
        await websocket.send_json({
            "type": "pong",
            "timestamp": time.time()
        })
    
    else:
        logger.warning(f"❓ Unknown message type: {message_type}")

# Global set to track active requests
active_requests = set()

async def generate_ai_response(session_id: str, character_id: str):
    """Generate AI response with REAL Rhubarb lip-sync"""

    request_key = f"{session_id}:{character_id}"
    if request_key in active_requests:
        logger.info(f"🚫 Duplicate request ignored for {character_id}")
        return
    
    active_requests.add(request_key)

    try:
        logger.info(f"🤖 Generating response for {character_id}")
        print(f"🎭 Character {character_id} is thinking...")
        
        # Get character instance
        character = get_character(character_id)
        topic = "artificial consciousness and the future of AI"
        
        # Generate character response"
        response_data = await character.generate_response(topic)
        
        print(f"💬 {character_id}: {response_data['text'][:100]}...")
        
        # RHUBARB LIP-SYNC GENERATION
        try:
            # Import TTS and lip-sync services
            from app.core.media.tts.google_tts import tts_service
            from app.core.media.tts.lip_sync import lip_sync_generator
            
            logger.info(f"🔄 Generating TTS with file for {character_id}...")
            
            # ✅ Generate TTS WITH FILE for Rhubarb
            tts_result = await tts_service.generate_speech_with_file(
                text=response_data["text"],
                character_id=character_id,
                emotion=response_data.get("facialExpression", "neutral")
            )
            
            if tts_result["success"] and "audioFilePath" in tts_result:
                # 🎭 REAL RHUBARB LIP-SYNC GENERATION
                logger.info(f"🎭 Generating REAL Rhubarb lip-sync for {character_id}...")
                print(f"🎤 Audio file: {os.path.basename(tts_result['audioFilePath'])}")
                
                # Generate lip-sync from audio file using Rhubarb
                lip_sync_result = await lip_sync_generator.generate_lip_sync_from_audio(
                    audio_file_path=tts_result["audioFilePath"],
                    text=response_data["text"]
                )
                
                # Clean up temporary audio file
                tts_service.cleanup_temp_file(tts_result["audioFilePath"])
                
                final_duration = tts_result.get("duration", response_data.get("duration", 3.0))
                final_audio_base64 = tts_result["audioBase64"]
                
                logger.info(f"✅ REAL Rhubarb lip-sync generated!")
                print(f"🎭 Rhubarb cues: {len(lip_sync_result['mouthCues'])} visemes")
                print(f"🎭 Sample cues: {lip_sync_result['mouthCues'][:3]}...")
                
            else:
                # Fallback if TTS with file failed
                logger.warning(f"TTS with file failed, using fallback for {character_id}")
                
                # Use old method as fallback
                tts_result_fallback = await tts_service.generate_speech(
                    text=response_data["text"],
                    character_id=character_id,
                    emotion=response_data.get("facialExpression", "neutral")
                )
                
                # Generate simple lip-sync
                lip_sync_result = await lip_sync_generator.generate_lip_sync(
                    text=response_data["text"],
                    duration=tts_result_fallback.get("duration", response_data.get("duration", 3.0))
                )
                
                final_duration = tts_result_fallback.get("duration", response_data.get("duration", 3.0))
                final_audio_base64 = tts_result_fallback["audioBase64"]
                
                logger.info(f"✅ Fallback lip-sync generated for {character_id}")
            
            logger.info(f"✅ TTS & Lip-sync completed for {character_id}")
            print(f"🎵 Audio: {len(final_audio_base64)} chars base64")
            print(f"👄 Lip-sync: {len(lip_sync_result['mouthCues'])} visemes")
            
        except Exception as tts_error:
            logger.error(f"❌ TTS/Lip-sync generation failed for {character_id}: {tts_error}")
            print(f"💥 TTS/Lip-sync Error: {tts_error}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic mock data
            final_duration = response_data.get("duration", 3.0)
            final_audio_base64 = "mock_audio_fallback"
            lip_sync_result = {
                "metadata": {"duration": final_duration}, 
                "mouthCues": [
                    {"start": 0.0, "end": final_duration, "value": "A"}
                ]
            }
            logger.warning(f"Using complete fallback for {character_id}")
        
        # complete message with ALL required fields
        complete_message = {
            # required fields that Node.js sends:
            "id": str(uuid.uuid4()),                           # Message ID
            "sessionId": session_id,                           # Session ID  
            "characterId": character_id,                       # Character ID
            "text": response_data["text"],                      # ✅ TEXT for subtitles!
            "facialExpression": response_data.get("facialExpression", "neutral"),
            "animation": "Talking_1",                          # Animation name
            "duration": final_duration,                        # ✅ DURATION for subtitles!
            "timestamp": int(time.time() * 1000),             # Timestamp in milliseconds
            
            # Audio/TTS fields:
            "audioBase64": final_audio_base64,                 # Audio data
            "lipSync": lip_sync_result,                        # ✅ REAL Rhubarb lip-sync data!
            "audioUrl": None,                                  # We use base64 streaming
            
            # Extra fields (optional but good to have):
            "personality_influence": response_data.get("personality_influence", {}),
            "energy_level": response_data.get("energy_level", 100.0),
            "resetExpressionAfter": True,  # Reset expression after speaking
        }

        try:
            from app.core.sessions.autonomous_manager import autonomous_session_manager

            session = autonomous_session_manager.get_session(session_id)
            if session:
                session.register_speech_start(
                    character_id=character_id,
                    text=response_data["text"],
                    duration=final_duration
                )
            logger.info(f"📝 Speech registered with autonomous session")
        except Exception as session_error:
            logger.debug(f"No autonomous session found or error: {session_error}")
        
        # 🐛 DEBUG: Print what we're sending
        print(f"📺 SUBTITLE & LIP-SYNC DEBUG:")
        print(f"   Character: {complete_message['characterId']}")
        print(f"   Text: '{complete_message['text'][:50]}...'")
        print(f"   Duration: {complete_message['duration']} seconds")
        print(f"   Audio: {len(complete_message['audioBase64'])} chars")
        print(f"   Lip-sync cues: {len(complete_message['lipSync']['mouthCues'])}")
        print(f"   First 3 cues: {complete_message['lipSync']['mouthCues'][:3]}")
        
        # response message
        response_message = {
            "type": "new_message",
            "sessionId": session_id,
            "data": {
                "message": complete_message 
            },
            "timestamp": int(time.time() * 1000)
        }
        
        # Send to all clients in session
        await manager.send_to_session(session_id, response_message)
        
        logger.info(f"✅ Complete response with REAL lip-sync sent for {character_id}")
        print(f"🚀 {character_id} finished speaking with Rhubarb lip-sync!")
        
    except Exception as e:
        logger.error(f"❌ AI response generation error for {character_id}: {e}")
        print(f"💥 Error generating response: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error message to frontend
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
        # Always remove from active requests
        active_requests.discard(request_key)