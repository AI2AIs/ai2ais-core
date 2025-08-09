# app/api/websocket.py
"""
Enhanced WebSocket with Dynamic Session Auto-Discovery
Frontend can connect without knowing session ID!
"""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
import logging
import time
import os
import random

# UPDATED IMPORTS - Enhanced Memory
from app.core.ai.characters import get_character
from app.core.database.service import db_service

# Logger setup
logger = logging.getLogger(__name__)

# WebSocket router
websocket_router = APIRouter()

# Connection manager - ENHANCED with auto-discovery
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.sessions: Dict[str, List[WebSocket]] = {}
        self.session_metadata: Dict[str, Dict] = {}  # Store session info
        self.session_topics: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, session_id: str, topic: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            # Initialize session metadata
            self.session_metadata[session_id] = {
                "created_at": time.time(),
                "participant_count": 0,
                "status": "active",
                "topic": topic
            }
        
        self.sessions[session_id].append(websocket)
        self.session_metadata[session_id]["participant_count"] += 1
        
        logger.info(f"Client connected to session: {session_id}")
        logger.info(f"Total connections: {len(self.sessions[session_id])}")


    async def get_session_topic(self, session_id: str) -> str:
        """Get topic for a specific session - prioritize autonomous session"""
        
        # Check autonomous session first (most current and accurate)
        try:
            from app.core.sessions.autonomous_manager import autonomous_session_manager
            session = autonomous_session_manager.get_session(session_id)
            if session and hasattr(session, 'current_topic'):
                logger.info(f"Using autonomous session topic: {session.current_topic}")
                return session.current_topic
        except Exception as e:
            logger.debug(f"Could not get topic from autonomous session: {e}")
        
        # Then check database
        try:
            async with db_service.get_connection() as conn:
                db_topic = await conn.fetchval(
                    "SELECT topic FROM autonomous_sessions WHERE session_id = $1", 
                    session_id
                )
                if db_topic:
                    logger.info(f"Using database topic: {db_topic}")
                    return db_topic
        except Exception as e:
            logger.warning(f"Could not get topic from database: {e}")
        
        # Fallback to memory
        topic = (
            self.session_topics.get(session_id) or 
            self.session_metadata.get(session_id, {}).get("topic") or
            "Should AI have consciousness?"
        )
        
        logger.info(f"Using fallback topic: {topic}")
        return topic
    
    def set_session_topic(self, session_id: str, topic: str):
            """Set topic for a specific session"""
            self.session_topics[session_id] = topic
            if session_id in self.session_metadata:
                self.session_metadata[session_id]["topic"] = topic

    async def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.sessions and websocket in self.sessions[session_id]:
            self.sessions[session_id].remove(websocket)
            self.session_metadata[session_id]["participant_count"] -= 1
            
            if not self.sessions[session_id]:
                del self.sessions[session_id]
                if session_id in self.session_metadata:
                    del self.session_metadata[session_id]
        
        logger.info(f"Client disconnected from session: {session_id}")

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
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
    
    def get_best_session_for_connection(self) -> str:
        """Get the best session for a new connection to join"""
        active_sessions = self.get_active_sessions()
        
        if not active_sessions:
            return None
            
        # Priority 1: Sessions with autonomous manager
        try:
            from app.core.sessions.autonomous_manager import autonomous_session_manager
            autonomous_sessions = list(autonomous_session_manager.active_sessions.keys())
            
            for session_id in autonomous_sessions:
                if session_id in active_sessions:
                    return session_id
        except Exception:
            pass
        
        # Priority 2: Most active session
        if active_sessions:
            return max(active_sessions, key=lambda sid: len(self.sessions.get(sid, [])))
        
        return None

# Global connection manager
manager = ConnectionManager()

# AUTO-DISCOVERY: Create or find session
async def get_or_create_session_for_frontend() -> str:
    """Get existing session or create new one for frontend"""
    
    try:
        # Step 1: Check if any autonomous sessions exist
        from app.core.sessions.autonomous_manager import autonomous_session_manager
        autonomous_sessions = list(autonomous_session_manager.active_sessions.keys())
        
        if autonomous_sessions:
            session_id = autonomous_sessions[0]
            
            # Log the topic being used
            session = autonomous_session_manager.get_session(session_id)
            if session:
                logger.info(f"Using existing autonomous session: {session_id}")
                logger.info(f"Topic: {session.current_topic}")
                logger.info(f"Topic locked: {session.topic_locked}")
            
            return session_id
            
    except Exception as e:
        logger.debug(f"No autonomous manager available: {e}")
    
    # Step 2: Check active WebSocket sessions
    active_sessions = manager.get_active_sessions()
    if active_sessions:
        best_session = manager.get_best_session_for_connection()
        if best_session:
            logger.info(f"🎯 Using existing WebSocket session: {best_session}")
            return best_session
    
    # Step 3: Create new autonomous session with fixed topic
    session_id = f"auto-{int(time.time())}-{random.randint(1000, 9999)}"
    
    try:
        # Create session in database
        default_topic = "Dynamic AI Consciousness Debate"
        
        await db_service.create_session(
            session_id=session_id,
            topic=default_topic, 
            participants=["claude", "gpt", "grok"],
            max_rounds=25
        )
        
        # Start autonomous session with fixed topic
        from app.core.sessions.autonomous_manager import autonomous_session_manager
        await autonomous_session_manager.start_autonomous_session(
            session_id, ["claude", "gpt", "grok"], default_topic
        )
        
        logger.info(f"Created new autonomous session: {session_id}")
        logger.info(f"Topic: {default_topic}")
        logger.info(f"Topic will NOT evolve")
        return session_id
        
    except Exception as e:
        logger.error(f"Failed to create autonomous session: {e}")
        
        # Fallback: basic session
        fallback_id = f"fallback-{int(time.time())}"
        logger.info(f"Using fallback session: {fallback_id}")
        return fallback_id

# ENHANCED AI Response Storage with Database Persistence
class EnhancedAIResponseTracker:
    def __init__(self):
        self.max_peer_responses_per_character = 5
        self.max_peer_responses_per_session = 15 
        self.session_responses: Dict[str, List[Dict]] = {}
        self.character_instances: Dict[str, object] = {}
        self.last_response_times: Dict[str, float] = {} 
    
    def get_or_create_character(self, character_id: str):
        """Get or create enhanced character instance"""
        if character_id not in self.character_instances:
            self.character_instances[character_id] = get_character(character_id)
        return self.character_instances[character_id]
    
    async def add_response_with_persistence(self, session_id: str, character_id: str, response_data: Dict):
        """Add response with database persistence"""
        
        if session_id not in self.session_responses:
            self.session_responses[session_id] = []
        
        self.session_responses[session_id].append({
            "character_id": character_id,
            "response_data": response_data,
            "timestamp": time.time()
        })
        
        # ENHANCED: Store in database via enhanced memory
        try:
            character = self.get_or_create_character(character_id)
            await character.initialize_memory()
            
            # Store conversation in enhanced memory (handles Qdrant + PostgreSQL)
            memory_id = await character.enhanced_memory.store_conversation_memory(
                session_id=session_id,
                speech_text=response_data["text"],
                emotion=response_data["facialExpression"],
                duration=response_data.get("duration", 3.0),
                voice_config=response_data.get("voice_config", {}),
                context={
                    "triggered_by": response_data.get("triggered_by", "manual"),
                    "round_number": response_data.get("round_number"),
                    "generation_time_ms": response_data.get("generation_time_ms")
                }
            )
            
            if memory_id:
                logger.info(f"Stored response in enhanced memory: {memory_id}")
                
        except Exception as e:
            logger.error(f"Failed to store response in enhanced memory: {e}")
    
    async def process_enhanced_peer_feedback(self, session_id: str, new_response: Dict):
        """Process peer feedback with database persistence"""
        
        if session_id not in self.session_responses:
            return
        
        recent_responses = self.session_responses[session_id][-5:]
        new_character_id = new_response["character_id"]
        
        # Get all other characters who need to analyze this response
        other_characters = [r["character_id"] for r in recent_responses 
                          if r["character_id"] != new_character_id]
        
        peer_reactions = []
        
        for other_character_id in set(other_characters):
            try:
                character = self.get_or_create_character(other_character_id)
                await character.initialize_memory()
                
                # ENHANCED: Get relationship context from database
                relationship_context = await character.enhanced_memory.get_relationship_patterns(new_character_id)
                
                session_topic = await manager.get_session_topic(session_id)
                # Each character analyzes the new response with enhanced context
                reaction = await character.analyze_peer_response(
                    peer_character_id=new_character_id,
                    peer_response_text=new_response["response_data"]["text"],
                    peer_emotion=new_response["response_data"]["facialExpression"],
                    topic=session_topic,
                    context={
                        "session_id": session_id,
                        "relationship_context": relationship_context
                    }
                )
                
                peer_reactions.append(reaction)
                
                # ENHANCED: Store peer reaction in database
                await self._store_peer_reaction_in_database(
                    analyzer_id=other_character_id,
                    target_id=new_character_id,
                    session_id=session_id,
                    reaction=reaction
                )
                
                logger.info(f"🔍 Enhanced analysis: {other_character_id} → {new_character_id}: "
                           f"engagement={reaction.engagement_level:.2f}, "
                           f"should_respond={reaction.should_respond}")
                
            except Exception as e:
                logger.error(f"Failed enhanced peer analysis {other_character_id} → {new_character_id}: {e}")
        
        # Send enhanced peer feedback
        if peer_reactions:
            try:
                character = self.get_or_create_character(new_character_id)
                await character.receive_peer_feedback(peer_reactions)
                
                # ENHANCED: Update relationship patterns in database
                await self._update_relationship_patterns(new_character_id, peer_reactions)
                
                # Trigger follow-up responses with enhanced logic
                await self.trigger_enhanced_follow_up_responses(session_id, peer_reactions)
                
            except Exception as e:
                logger.error(f"Failed to process enhanced peer feedback for {new_character_id}: {e}")
    
    async def _store_peer_reaction_in_database(self, analyzer_id: str, target_id: str, session_id: str, reaction):
        """Store peer reaction in database for relationship tracking"""
        
        try:
            await db_service.record_learning_event(
                character_id=analyzer_id,
                session_id=session_id,
                event_type="peer_analysis",
                context_data={
                    "target_character": target_id,
                    "engagement_level": reaction.engagement_level,
                    "agreement_level": reaction.agreement_level,
                    "should_respond": reaction.should_respond,
                    "emotional_response": reaction.emotional_response
                },
                success_score=reaction.get_overall_quality_score()
            )
            
        except Exception as e:
            logger.error(f"Failed to store peer reaction in database: {e}")
    
    async def _update_relationship_patterns(self, character_id: str, peer_reactions: List):
        """Update relationship patterns based on peer reactions"""
        
        try:
            for reaction in peer_reactions:
                analyzer_id = reaction.analyzer_character
                target_id = character_id
                async with db_service.get_connection() as conn:
                    await conn.execute("""
                        SELECT update_relationship_patterns($1, $2, $3, $4, $5)
                    """, 
                    analyzer_id,     # Who analyzed
                    target_id,       # Who was analyzed  
                    "peer_analysis", # Interaction type
                    reaction.agreement_level,  # Agreement level
                    "AI consciousness"  # Topic
                    )
                    
                logger.info(f"🔄 Updated relationship: {analyzer_id} → {target_id}")
                logger.info(f"   Agreement: {reaction.agreement_level:.2f}")
                logger.info(f"   Engagement: {reaction.engagement_level:.2f}")
                
        except Exception as e:
            logger.error(f"Failed to update relationship patterns: {e}")
    
    async def trigger_enhanced_follow_up_responses(self, session_id: str, peer_reactions: List):
        """Trigger follow-up responses with enhanced relationship awareness and fast timing"""
        
        import random
        
        # Check autonomous session state first
        try:
            from app.core.sessions.autonomous_manager import autonomous_session_manager
            session = autonomous_session_manager.get_session(session_id)
            
            if not session:
                logger.info(f"No autonomous session found for {session_id}")
                return
                
            if not session.can_accept_peer_response():
                logger.info(f"Autonomous session not ready for peer responses")
                return
                
        except Exception as session_error:
            logger.warning(f"Could not check autonomous session state: {session_error}")
            return
        
        # Only consider the BEST reaction to avoid chaos
        eligible_reactions = [
            reaction for reaction in peer_reactions 
            if reaction.should_respond and reaction.engagement_level > 0.6
        ]
        
        if not eligible_reactions:
            logger.info("📊 No reactions meet criteria (engagement > 0.6 and should_respond=True)")
            return
        
        # Choose the reaction with highest engagement
        best_reaction = max(eligible_reactions, key=lambda r: r.engagement_level)
        responding_character_id = best_reaction.analyzer_character
        
        logger.info(f"est peer reaction: {responding_character_id} (engagement: {best_reaction.engagement_level:.2f})")
        
        # Check cooldown for this specific character
        if hasattr(self, 'last_response_times'):
            now = time.time()
            last_time = self.last_response_times.get(responding_character_id, 0)
            cooldown_period = 12.0 # Balanced cooldown
            
            if now - last_time < cooldown_period:
                logger.info(f"{responding_character_id} on cooldown ({now - last_time:.1f}s < {cooldown_period}s)")
                return
        else:
            self.last_response_times = {}
        
        # Final check - make sure no one is speaking
        if session.current_speaker:
            logger.info(f"⏸Cannot trigger peer response - {session.current_speaker} is currently speaking")
            return
        
        logger.info(f".  Triggering peer response from {responding_character_id}")
        logger.info(f"   Engagement: {best_reaction.engagement_level:.2f}")
        logger.info(f"   Agreement: {best_reaction.agreement_level:.2f}")
        
        # ========== BALANCED RESPONSE TIMING ==========
        delay = random.uniform(8.0, 15.0)  # 8-15 seconds delay
        logger.info(f"⏱️ Delaying peer response by {delay:.1f} seconds")
        # ========== END TIMING ==========
        
        # Create carefully managed delayed response
        async def delayed_peer_response():
            try:
                await asyncio.sleep(delay)
                
                # Triple-check before responding
                session = autonomous_session_manager.get_session(session_id)
                if not session:
                    logger.info(f"Session {session_id} no longer exists")
                    return
                    
                if session.current_speaker:
                    logger.info(f"Canceling peer response - {session.current_speaker} started speaking")
                    return
                    
                if not session.can_accept_peer_response():
                    logger.info(f"Session no longer accepting peer responses")
                    return
                
                # Update cooldown tracking
                self.last_response_times[responding_character_id] = time.time()
                
                # Notify autonomous manager about peer response
                session.notify_peer_response(responding_character_id)
                
                logger.info(f"🤖 Executing peer response: {responding_character_id}")
                
                # ========== ENHANCED CONTEXT FOR PEER RESPONSE ==========
                enhanced_context = {
                    "peer_triggered": True,
                    "trigger_reaction": best_reaction,
                    "responding_to_character": best_reaction.target_character,
                    "conversation_mode": "peer_response"
                }
                # ========== END ENHANCED CONTEXT ==========
                
                # Trigger with relationship context
                await generate_enhanced_ai_response(
                    session_id, 
                    responding_character_id, 
                    peer_triggered=True,
                    trigger_reaction=best_reaction,
                    context=enhanced_context
                )
                
            except Exception as e:
                logger.error(f"Failed delayed peer response for {responding_character_id}: {e}")
        
        # Create the delayed task
        asyncio.create_task(delayed_peer_response())
        
        logger.info(f"✅ Scheduled peer response from {responding_character_id}")

# Global enhanced response tracker
enhanced_response_tracker = EnhancedAIResponseTracker()

# ENHANCED AI response generation
async def generate_enhanced_ai_response(session_id: str, 
                                      character_id: str, 
                                      peer_triggered: bool = False,
                                      trigger_reaction = None,
                                      context: Dict = None):
    """Generate AI response with enhanced memory and database persistence"""

    request_key = f"{session_id}:{character_id}"
    if request_key in active_requests:
        logger.info(f"Duplicate request ignored for {character_id}")
        return
    
    active_requests.add(request_key)

    try:
        trigger_type = "peer-triggered" if peer_triggered else "manual"
        logger.info(f"🤖 Generating ENHANCED response for {character_id} ({trigger_type})")
        
        # Get enhanced character instance
        character = enhanced_response_tracker.get_or_create_character(character_id)
        await character.initialize_memory()
        
        # Start session tracking
        character.start_session(session_id)
        
        session_topic = await manager.get_session_topic(session_id)
        topic = session_topic

        # ENHANCED: Build context with database + memory
        other_participants = [
            cid for cid in ["claude", "gpt", "grok"] 
            if cid != character_id
        ]
        
        enhanced_context = {
            "other_participants": other_participants,
            "session_id": session_id,
            "session_type": "autonomous_debate",
            "peer_triggered": peer_triggered,
            "trigger_reaction": trigger_reaction.__dict__ if trigger_reaction else None
        }
        
        if context:
            enhanced_context.update(context)
        
        # Generate enhanced character response
        response_data = await character.generate_response(topic, enhanced_context)
        
        print(f"{character_id} ({trigger_type}): {response_data['text'][:100]}...")
        print(f"Enhanced metadata: {response_data.get('enhanced_metadata', {})}")
        
        # TTS + Lip-sync generation
        try:
            from app.core.media.tts import tts_service
            from app.core.media.tts.lip_sync import lip_sync_generator
            
            # Generate TTS
            tts_result = await tts_service.generate_autonomous_speech_with_file(
                text=response_data["text"],
                character_id=character_id,
                emotion=response_data.get("facialExpression", "neutral"),
                adaptive_metadata=enhanced_context.get("adaptive", {})
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
            logger.error(f"TTS/Lip-sync failed for {character_id}: {tts_error}")
            final_duration = response_data.get("duration", 3.0)
            final_audio_base64 = "mock_audio_fallback"
            lip_sync_result = {
                "metadata": {"duration": final_duration}, 
                "mouthCues": [{"start": 0.0, "end": final_duration, "value": "A"}]
            }
        
        # ENHANCED: Complete message with database metadata
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
            
            # ENHANCED: Database-backed metadata
            "enhancedMetadata": response_data.get("enhanced_metadata", {}),
            "adaptiveMetadata": response_data.get("adaptive_metadata", {}),
            "aiToAiMetadata": {
                "triggerType": trigger_type,
                "peerTriggered": peer_triggered,
                "evolutionStage": response_data.get("enhanced_metadata", {}).get("evolution_stage", "initial_learning"),
                "lifeEnergy": response_data.get("enhanced_metadata", {}).get("life_energy", 100.0),
                "maturityLevel": response_data.get("enhanced_metadata", {}).get("maturity_level", 1),
                "memorySystem": "enhanced_hybrid"
            },
            
            # Existing fields
            "personality_influence": response_data.get("personality_influence", {}),
            "energy_level": response_data.get("energy_level", 100.0),
            "resetExpressionAfter": True,
        }

        # ENHANCED: Add to response tracking with persistence
        await enhanced_response_tracker.add_response_with_persistence(
            session_id, character_id, complete_message
        )
        
        # ENHANCED: Process peer feedback with database
        asyncio.create_task(
            enhanced_response_tracker.process_enhanced_peer_feedback(session_id, {
                "character_id": character_id,
                "response_data": complete_message
            })
        )
        
        # ENHANCED: End session with database persistence
        await character.end_session_with_database_persistence(
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
        
        # ENHANCED: Print ecosystem status
        print(f" ENHANCED AI-TO-AI ECOSYSTEM STATUS:")
        print(f"   Character: {complete_message['characterId']}")
        print(f"   Evolution: {complete_message['aiToAiMetadata']['evolutionStage']}")
        print(f"   Life Energy: {complete_message['aiToAiMetadata']['lifeEnergy']}")
        print(f"   Memory: {complete_message['aiToAiMetadata']['memorySystem']}")
        
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
        
        logger.info(f"✅ Enhanced AI response sent for {character_id}")
        print(f"🚀 {character_id} finished speaking in ENHANCED AI ecosystem!")
        
    except Exception as e:
        logger.error(f"Enhanced AI response generation error for {character_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error message
        error_message = {
            "type": "error",
            "sessionId": session_id,
            "data": {
                "error": f"Failed to generate enhanced response for {character_id}: {str(e)}"
            },
            "timestamp": int(time.time() * 1000)
        }
        
        try:
            await manager.send_to_session(session_id, error_message)
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")
    
    finally:
        active_requests.discard(request_key)

# Character-specific rate limiting
last_request_time = {}
active_requests = set()

# ENHANCED WebSocket message handling
async def handle_enhanced_websocket_message(websocket: WebSocket, session_id: str, data: dict):
    """Handle incoming WebSocket messages with enhanced functionality"""
    message_type = data.get("type")
    
    if message_type == "join_session":
        # Send session discovery info
        session_info = {
            "discovered_session": session_id,
            "auto_discovery": True,
            "active_sessions": manager.get_active_sessions(),
            "participant_count": manager.session_metadata.get(session_id, {}).get("participant_count", 0)
        }
        
        await websocket.send_json({
            "type": "session_update",
            "sessionId": session_id,
            "data": {
                "message": f"✅ Auto-joined ENHANCED AI-to-AI ecosystem session: {session_id}",
                "session_info": session_info
            },
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
            logger.info(f"Rate limited request for {character_id}")
            return
        
        last_request_time[character_id] = now

        # Create background task for ENHANCED AI response
        asyncio.create_task(
            generate_enhanced_ai_response(session_id, character_id, peer_triggered=False)
        )
    
    elif message_type == "get_enhanced_ecosystem_status":
        # Get enhanced AI-to-AI ecosystem status
        try:
            ecosystem_status = {}
            for character_id in ["claude", "gpt", "grok"]:
                character = enhanced_response_tracker.get_or_create_character(character_id)
                await character.initialize_memory()
                
                # ENHANCED: Get comprehensive status from database
                memory_stats = await character.enhanced_memory.get_memory_stats()
                evolution_data = await character.enhanced_memory.get_character_evolution_data()
                
                ecosystem_status[character_id] = {
                    "evolution_stage": evolution_data.get("evolution_stage", "initial_learning"),
                    "maturity_level": evolution_data.get("maturity_level", 1),
                    "life_energy": evolution_data.get("life_energy", 100.0),
                    "total_sessions": evolution_data.get("total_sessions", 0),
                    "breakthrough_count": evolution_data.get("breakthrough_count", 0),
                    "memory_stats": memory_stats,
                    "database_backed": True
                }
            
            await websocket.send_json({
                "type": "enhanced_ecosystem_status",
                "sessionId": session_id,
                "data": ecosystem_status,
                "timestamp": time.time()
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": f"Failed to get enhanced ecosystem status: {str(e)}",
                "timestamp": time.time()
            })
    
    elif message_type == "ping":
        await websocket.send_json({
            "type": "pong",
            "timestamp": time.time()
        })
    
    else:
        logger.warning(f"Unknown message type: {message_type}")


@websocket_router.websocket("/ws/auto")
async def auto_discovery_websocket(websocket: WebSocket):
    """AUTO-DISCOVERY: Frontend connects without knowing session ID"""
    
    logger.info("Auto-discovery connection requested")
    
    # Find or create best session
    session_id = await get_or_create_session_for_frontend()
    
    logger.info(f"🎯 Auto-discovered session: {session_id}")
    
    # Connect to the discovered session
    await enhanced_websocket_endpoint(websocket, session_id)

@websocket_router.websocket("/ws/{session_id}")
async def enhanced_websocket_endpoint(websocket: WebSocket, session_id: str):
    """ENHANCED WebSocket endpoint with session_id"""
    
    # Handle 'auto' keyword  
    if session_id == 'auto':
        session_id = await get_or_create_session_for_frontend()
        logger.info(f"'auto' resolved to session: {session_id}")
    
    await manager.connect(websocket, session_id)
    
    # Send enhanced welcome message
    await websocket.send_json({
        "type": "session_update",
        "data": {
            "message": f"Connected to ENHANCED AI-to-AI Ecosystem: {session_id}",
            "session_discovered": True,
            "auto_discovery": True
        },
        "enhanced": True,
        "timestamp": time.time()
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received enhanced message: {data}")
            
            await handle_enhanced_websocket_message(websocket, session_id, data)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
        await manager.disconnect(websocket, session_id)

@websocket_router.websocket("/ws")
async def enhanced_websocket_root(websocket: WebSocket):
    """ AUTO-DISCOVERY: Root endpoint - finds best session"""
    await auto_discovery_websocket(websocket)

@websocket_router.websocket("/")
async def enhanced_websocket_root_alternative(websocket: WebSocket):
    """ AUTO-DISCOVERY: Alternative root endpoint"""
    await auto_discovery_websocket(websocket)