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
        
        # Autonomous behavior settings
        self.min_silence_duration = 2.0  # Minimum 2 seconds between speeches
        self.max_silence_duration = 8.0  # Maximum 8 seconds silence
        self.conversation_rounds = 0
        self.max_rounds = 20  # Auto-stop after 20 rounds
        
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
        
        
        # Initial speaker
        await asyncio.sleep(3.0)
        await self._trigger_next_speaker()
        
        while self._running and not self._stop_requested:
            try:
                await self._autonomous_tick()
                await asyncio.sleep(1.0)  # Check every second
                
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
        
        # Check if we should trigger next speaker
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
        return time.time() >= latest_speech.end_time
    
    def _should_trigger_next_speaker(self, current_time: float) -> bool:
        """Determine if we should trigger the next speaker"""
        if self.current_speaker:  # Someone is speaking
            return False
            
        time_since_last = current_time - self.last_speech_end
        
        # Minimum silence elapsed
        if time_since_last < self.min_silence_duration:
            return False
        
        # Random trigger within silence window
        silence_window = self.max_silence_duration - self.min_silence_duration
        trigger_threshold = self.min_silence_duration + (random.random() * silence_window)
        
        return time_since_last >= trigger_threshold
    
    async def _trigger_next_speaker(self):
        """Trigger the next speaker intelligently"""
        # Choose next speaker intelligently
        next_speaker = self._choose_next_speaker()
        
        if next_speaker:
            logger.info(f"🎤 Triggering {next_speaker} to speak")
            await self._request_character_speech(next_speaker)
    
    def _choose_next_speaker(self) -> str:
        """Intelligently choose the next speaker"""
        # Priority queue first
        if self.speech_queue:
            return self.speech_queue.pop(0)
        
        # Avoid same speaker twice in a row
        available_speakers = [p for p in self.participants if p != self.current_speaker]
        
        if not available_speakers:
            available_speakers = self.participants
        
        # Choose based on recent activity (least recent gets priority)
        if self.speech_history:
            recent_speakers = [event.character_id for event in self.speech_history[-3:]]
            non_recent = [s for s in available_speakers if s not in recent_speakers]
            if non_recent:
                available_speakers = non_recent
        
        return random.choice(available_speakers)
    
    async def _request_character_speech(self, character_id: str):
        """Request a character to speak"""
        from app.api.websocket import generate_enhanced_ai_response as generate_ai_response

        
        self.current_speaker = character_id
        self.conversation_rounds += 1

        # Temporary speech event (will be updated with real data)
        temp_speech = SpeechEvent(
        character_id=character_id,
        start_time=time.time(),
        duration=5.0,  # Estimated
        text="generating..."
        )
        self.speech_history.append(temp_speech)
        
        # Start speech generation in background
        asyncio.create_task(generate_enhanced_ai_response(self.session_id, character_id, peer_triggered=False))
    
    def register_speech_start(self, character_id: str, text: str, duration: float):
        """Register when a character starts speaking"""
        speech_event = SpeechEvent(
            character_id=character_id,
            start_time=time.time(),
            duration=duration,
            text=text
        )
        
        self.speech_history.append(speech_event)
        self.current_speaker = character_id
        
        logger.info(f"🎤 Speech registered: {character_id} for {duration}s")
    
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

# Global session manager
autonomous_session_manager = AutonomousSessionManager()