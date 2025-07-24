# app/core/sessions/autonomous_manager.py
import asyncio
import logging
import time
import random
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from app.api.websocket import generate_enhanced_ai_response

logger = logging.getLogger(__name__)

class SessionState(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

@dataclass
class SpeechEvent:
    character_id: str
    start_time: float
    duration: float
    text: str
    
    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

class AutonomousSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, 'AutonomousSession'] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def start_autonomous_session(self, session_id: str, participants: List[str]) -> 'AutonomousSession':
        """Start a new autonomous debate session"""
        if session_id in self.active_sessions:
            await self.stop_session(session_id)
        
        session = AutonomousSession(session_id, participants)
        self.active_sessions[session_id] = session
        
        # Start the session loop
        asyncio.create_task(session.run_autonomous_loop())
        
        logger.info(f"🎭 Started autonomous session: {session_id}")
        return session
    
    async def stop_session(self, session_id: str):
        """Stop an autonomous session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            await session.stop()
            del self.active_sessions[session_id]
            logger.info(f"🛑 Stopped autonomous session: {session_id}")
    
    async def handle_manual_request(self, session_id: str, character_id: str):
        """Handle manual character request (from frontend)"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            await session.queue_character_speech(character_id, priority=True)
    
    def get_session(self, session_id: str) -> Optional['AutonomousSession']:
        return self.active_sessions.get(session_id)

class AutonomousSession:
    def __init__(self, session_id: str, participants: List[str]):
        self.session_id = session_id
        self.participants = participants
        self.state = SessionState.IDLE
        
        # Speech management
        self.current_speaker: Optional[str] = None
        self.speech_queue: List[str] = []
        self.speech_history: List[SpeechEvent] = []
        self.last_speech_end = 0.0
        
        # conservative timing to prevent overlap with peer system
        self.min_silence_duration = 10.0  # Increased from 2.0 to 10.0 seconds
        self.max_silence_duration = 20.0  # Increased from 8.0 to 20.0 seconds
        self.conversation_rounds = 0
        self.max_rounds = 20  # Auto-stop after 20 rounds
        self.max_total_speeches = 50
        self.max_session_duration = 3600.0  # 1 hour max session duration
        self.total_speeches = 0
        self.session_start_time = time.time()
        
        # Add peer system coordination
        self.peer_system_active = True  # Allow peer system to take priority
        self.last_peer_response_time = 0.0
        self.peer_cooldown = 30.0  # 30 seconds before autonomous kicks in after peer response
        
        # Topic management
        self.current_topic = "artificial consciousness and the future of AI"
        self.topic_evolution_counter = 0
        
        # Control flags
        self._running = False
        self._stop_requested = False
        
    async def run_autonomous_loop(self):
        """Main autonomous session loop"""
        self.state = SessionState.ACTIVE
        self._running = True
        
        logger.info(f"🎭 Starting autonomous loop for session: {self.session_id}")        
        
        # 🔥 FIXED: Longer initial delay to let peer system settle
        await asyncio.sleep(5.0)  # Increased from 3.0 to 5.0
        await self._trigger_next_speaker()
        
        while self._running and not self._stop_requested:
            try:
                await self._autonomous_tick()
                await asyncio.sleep(2.0)  # Increased from 1.0 to 2.0 seconds check interval
                
            except Exception as e:
                logger.error(f"Error in autonomous loop: {e}")
                await asyncio.sleep(5.0)  # Wait before retrying
        
        self.state = SessionState.ENDED
        logger.info(f"🏁 Autonomous loop ended for session: {self.session_id}")
    
    async def _autonomous_tick(self):
        """Single tick of autonomous behavior"""
        current_time = time.time()
        
        # Check if someone is currently speaking
        if self.current_speaker:
            # Check if speech should have ended
            if self._is_current_speech_finished():
                logger.info(f"🔇 Speech finished for {self.current_speaker}")
                self.current_speaker = None
                self.last_speech_end = current_time
                
                # Evolve topic occasionally
                if self.conversation_rounds % 5 == 0:
                    await self._evolve_topic()
        
        # 🔥 FIXED: Check if we should trigger next speaker with peer system coordination
        elif self._should_trigger_next_speaker(current_time):
            await self._trigger_next_speaker()
        
        # Check for session completion
        if self.conversation_rounds >= self.max_rounds:
            logger.info(f"🏁 Max rounds reached, ending session {self.session_id}")
            await self.stop()
    
    def _is_current_speech_finished(self) -> bool:
        """Check if current speech has finished based on timing"""
        if not self.speech_history:
            return True
            
        latest_speech = self.speech_history[-1]
        is_finished = time.time() >= latest_speech.end_time
        
        # 🔥 FIXED: Add buffer time to ensure speech actually finished
        if is_finished:
            buffer_time = 2.0  # 2 second buffer
            return time.time() >= (latest_speech.end_time + buffer_time)
        
        return False
    
    def _should_trigger_next_speaker(self, current_time: float) -> bool:
        """Determine if we should trigger the next speaker"""
        if self.current_speaker:  # Someone is speaking
            return False
        
        # 🔥 FIXED: Check if peer system recently responded
        if self.peer_system_active:
            time_since_peer = current_time - self.last_peer_response_time
            if time_since_peer < self.peer_cooldown:
                logger.debug(f"🤖 Waiting for peer system cooldown ({time_since_peer:.1f}s < {self.peer_cooldown}s)")
                return False
            
        time_since_last = current_time - self.last_speech_end
        
        # Minimum silence elapsed
        if time_since_last < self.min_silence_duration:
            return False
        
        # 🔥 FIXED: More conservative random trigger
        silence_window = self.max_silence_duration - self.min_silence_duration
        trigger_threshold = self.min_silence_duration + (random.random() * silence_window)
        
        should_trigger = time_since_last >= trigger_threshold
        
        if should_trigger:
            logger.info(f"⏰ Autonomous trigger: {time_since_last:.1f}s silence >= {trigger_threshold:.1f}s threshold")
        
        return should_trigger
    
    async def _trigger_next_speaker(self):
        """Trigger the next speaker intelligently"""
        # 🔥 FIXED: Double-check no one is speaking before triggering
        if self.current_speaker:
            logger.info(f"🚫 Canceling trigger - {self.current_speaker} is still speaking")
            return
            
        # Choose next speaker intelligently
        next_speaker = self._choose_next_speaker()
        
        if next_speaker:
            logger.info(f"🎤 Autonomous triggering {next_speaker} to speak")
            await self._request_character_speech(next_speaker)
    
    def _choose_next_speaker(self) -> str:
        """Intelligently choose the next speaker"""
        # Priority queue first
        if self.speech_queue:
            speaker = self.speech_queue.pop(0)
            logger.info(f"📋 Using queued speaker: {speaker}")
            return speaker
        
        # Avoid same speaker twice in a row
        available_speakers = [p for p in self.participants if p != self.current_speaker]
        
        if not available_speakers:
            available_speakers = self.participants
        
        # 🔥 FIXED: More intelligent speaker selection
        if self.speech_history:
            # Get last 5 speakers instead of 3 for better distribution
            recent_speakers = [event.character_id for event in self.speech_history[-5:]]
            speaker_counts = {speaker: recent_speakers.count(speaker) for speaker in self.participants}
            
            # Choose speaker who spoke least recently
            least_active = min(speaker_counts.items(), key=lambda x: x[1])
            if least_active[0] in available_speakers:
                logger.info(f"🎯 Choosing least active speaker: {least_active[0]} (spoke {least_active[1]} times recently)")
                return least_active[0]
        
        selected = random.choice(available_speakers)
        logger.info(f"🎲 Random speaker selection: {selected}")
        return selected
    
    async def _request_character_speech(self, character_id: str):
        """Request a character to speak"""
        from app.api.websocket import generate_enhanced_ai_response as generate_ai_response
        
        # 🔥 FIXED: More robust speaker management
        if self.current_speaker:
            logger.warning(f"⚠️ Attempting to start {character_id} while {self.current_speaker} is speaking")
            return
        
        self.current_speaker = character_id
        self.conversation_rounds += 1

        # Create speech event with realistic duration estimate
        estimated_duration = random.uniform(15.0, 25.0)  # More realistic 15-25 seconds
        speech_event = SpeechEvent(
            character_id=character_id,
            start_time=time.time(),
            duration=estimated_duration,
            text="generating..."
        )
        self.speech_history.append(speech_event)
        
        logger.info(f"🎤 Autonomous request: {character_id} (Round {self.conversation_rounds})")
        
        # Start speech generation in background
        asyncio.create_task(generate_enhanced_ai_response(self.session_id, character_id, peer_triggered=False))
    
    def register_speech_start(self, character_id: str, text: str, duration: float):
        """Register when a character starts speaking"""
        # 🔥 FIXED: Update the most recent speech event with actual data
        if self.speech_history and self.speech_history[-1].character_id == character_id:
            # Update the temporary speech event with real data
            self.speech_history[-1] = SpeechEvent(
                character_id=character_id,
                start_time=time.time(),
                duration=duration,
                text=text
            )
        else:
            # Add new speech event if not found
            speech_event = SpeechEvent(
                character_id=character_id,
                start_time=time.time(),
                duration=duration,
                text=text
            )
            self.speech_history.append(speech_event)
        
        self.current_speaker = character_id
        
        logger.info(f"🎤 Speech registered: {character_id} for {duration}s")
        logger.info(f"📝 Text: {text[:100]}...")
    
    # 🔥 NEW: Method to notify when peer system responds
    def notify_peer_response(self, character_id: str):
        """Notify that peer system triggered a response"""
        self.last_peer_response_time = time.time()
        logger.info(f"🤖 Peer system response noted: {character_id}")
    
    async def queue_character_speech(self, character_id: str, priority: bool = False):
        """Queue a character to speak"""
        if priority:
            self.speech_queue.insert(0, character_id)
        else:
            self.speech_queue.append(character_id)
        
        logger.info(f"📝 Queued {character_id} to speak (priority: {priority})")
    
    async def _evolve_topic(self):
        """Evolve the conversation topic"""
        self.topic_evolution_counter += 1
        
        topic_variations = [
            "the ethical implications of AI consciousness",
            "whether machines can truly understand emotions",
            "the future of human-AI collaboration",
            "the risks and benefits of superintelligent AI",
            "how AI might change the nature of work and society"
        ]
        
        if self.topic_evolution_counter < len(topic_variations):
            self.current_topic = topic_variations[self.topic_evolution_counter]
            logger.info(f"🔄 Topic evolved to: {self.current_topic}")
    
    async def stop(self):
        """Stop the autonomous session"""
        self._stop_requested = True
        self._running = False
        self.state = SessionState.ENDED
        logger.info(f"🛑 Stopping session {self.session_id}")
    
    # 🔥 NEW: Method to check if session is in a good state for peer responses
    def can_accept_peer_response(self) -> bool:
        """Check if session can accept a peer-triggered response"""
        if self.current_speaker:
            return False  # Someone is already speaking
        
        # Check if we just had a speech end
        if self.last_speech_end > 0:
            time_since_last = time.time() - self.last_speech_end
            if time_since_last < 3.0:  # 3 second grace period
                return False
        
        return True

# Global session manager
autonomous_session_manager = AutonomousSessionManager()