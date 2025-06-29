# app/core/media/tts/google_tts.py
import base64
import json
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any
import tempfile
import os
import struct
import time

from app.config.settings import settings
from .voice_profiles import get_voice_config

logger = logging.getLogger(__name__)

class GoogleTTSService:
    def __init__(self):
        self.api_key = settings.GOOGLE_TTS_API_KEY
        self.base_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        
    async def generate_speech(
        self, 
        text: str, 
        character_id: str = "claude",
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """Generate speech using Google TTS (base64 only)"""
        
        if not self.api_key:
            logger.warning("Google TTS API key not found, using mock audio")
            return await self._generate_mock_audio(text, character_id)
        
        try:
            voice_config = get_voice_config(character_id)
            
            # Emotion-based modifications
            speaking_rate = voice_config["config"]["speakingRate"]
            pitch = voice_config["config"]["pitch"]
            
            if emotion == "excited":
                speaking_rate *= 1.2
                pitch += 3.0
            elif emotion == "concerned":
                speaking_rate *= 0.8
                pitch -= 2.0
            elif emotion == "confident":
                speaking_rate *= 1.1
                pitch += 1.0
                
            # Prepare request
            request_body = {
                "input": {"text": text},
                "voice": {
                    "languageCode": voice_config["config"]["languageCode"],
                    "name": voice_config["config"]["name"],
                    "ssmlGender": voice_config["config"]["ssmlGender"]
                },
                "audioConfig": {
                    "audioEncoding": "LINEAR16",
                    "sampleRateHertz": 22050,
                    "speakingRate": min(4.0, max(0.25, speaking_rate)),
                    "pitch": min(20.0, max(-20.0, pitch)),
                    "volumeGainDb": 0.0
                }
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google TTS API error: {response.status_code} - {response.text}")
                    return await self._generate_mock_audio(text, character_id)
                
                data = response.json()
                audio_content = data.get("audioContent")
                
                if not audio_content:
                    logger.error("No audio content received from Google TTS")
                    return await self._generate_mock_audio(text, character_id)
                
                # Calculate duration (rough estimate)
                duration = len(text) * 0.05 + 1.0
                
                logger.info(f"✅ Google TTS generated for {character_id}: {len(text)} chars")
                
                return {
                    "success": True,
                    "audioBase64": audio_content,
                    "duration": round(duration, 2),
                    "provider": "google_tts",
                    "character_id": character_id,
                    "emotion": emotion
                }
                
        except Exception as e:
            logger.error(f"TTS generation failed for {character_id}: {e}")
            return await self._generate_mock_audio(text, character_id)

    # Generate speech with file output for Rhubarb
    async def generate_speech_with_file(
        self, 
        text: str, 
        character_id: str = "claude",
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """Generate speech using Google TTS and save to file for Rhubarb lip-sync"""
        
        if not self.api_key:
            logger.warning("Google TTS API key not found, using mock audio with file")
            return await self._generate_mock_audio_with_file(text, character_id)
        
        try:
            voice_config = get_voice_config(character_id)
            
            # Emotion-based modifications
            speaking_rate = voice_config["config"]["speakingRate"]
            pitch = voice_config["config"]["pitch"]
            
            if emotion == "excited":
                speaking_rate *= 1.2
                pitch += 3.0
            elif emotion == "concerned":
                speaking_rate *= 0.8
                pitch -= 2.0
            elif emotion == "confident":
                speaking_rate *= 1.1
                pitch += 1.0
                
            # Prepare request
            request_body = {
                "input": {"text": text},
                "voice": {
                    "languageCode": voice_config["config"]["languageCode"],
                    "name": voice_config["config"]["name"],
                    "ssmlGender": voice_config["config"]["ssmlGender"]
                },
                "audioConfig": {
                    "audioEncoding": "LINEAR16",
                    "sampleRateHertz": 22050,
                    "speakingRate": min(4.0, max(0.25, speaking_rate)),
                    "pitch": min(20.0, max(-20.0, pitch)),
                    "volumeGainDb": 0.0
                }
            }
            
            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google TTS API error: {response.status_code} - {response.text}")
                    return await self._generate_mock_audio_with_file(text, character_id)
                
                data = response.json()
                audio_content = data.get("audioContent")
                
                if not audio_content:
                    logger.error("No audio content received from Google TTS")
                    return await self._generate_mock_audio_with_file(text, character_id)
                
                # ✅ SAVE TO FILE FOR RHUBARB
                audio_file_path = await self._save_audio_to_file(audio_content, character_id)
                
                # Calculate duration
                duration = len(text) * 0.05 + 1.0
                
                logger.info(f"✅ Google TTS with file generated for {character_id}: {os.path.basename(audio_file_path)}")
                
                return {
                    "success": True,
                    "audioBase64": audio_content,
                    "audioFilePath": audio_file_path,  # ← NEW: For Rhubarb
                    "duration": round(duration, 2),
                    "provider": "google_tts",
                    "character_id": character_id,
                    "emotion": emotion
                }
                
        except Exception as e:
            logger.error(f"TTS with file generation failed for {character_id}: {e}")
            return await self._generate_mock_audio_with_file(text, character_id)

    async def _save_audio_to_file(self, audio_base64: str, character_id: str) -> str:
        """Save Google TTS audio to WAV file for Rhubarb"""
        
        try:
            # Create temporary file path
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            audio_filename = f"tts_{character_id}_{timestamp}.wav"
            audio_file_path = os.path.join(temp_dir, audio_filename)
            
            # Decode base64 audio (raw LINEAR16 from Google)
            audio_bytes = base64.b64decode(audio_base64)
            
            # Create proper WAV file with header
            sample_rate = 22050
            num_channels = 1
            bits_per_sample = 16
            num_samples = len(audio_bytes) // 2  # 16-bit = 2 bytes per sample
            
            # WAV header
            wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                b'RIFF',                                    # ChunkID
                36 + len(audio_bytes),                      # ChunkSize
                b'WAVE',                                    # Format
                b'fmt ',                                    # Subchunk1ID
                16,                                         # Subchunk1Size (PCM)
                1,                                          # AudioFormat (PCM)
                num_channels,                               # NumChannels
                sample_rate,                                # SampleRate
                sample_rate * num_channels * bits_per_sample // 8,  # ByteRate
                num_channels * bits_per_sample // 8,        # BlockAlign
                bits_per_sample,                            # BitsPerSample
                b'data',                                    # Subchunk2ID
                len(audio_bytes)                            # Subchunk2Size
            )
            
            # Write WAV file
            with open(audio_file_path, 'wb') as f:
                f.write(wav_header + audio_bytes)
            
            logger.info(f"💾 Audio saved to: {audio_file_path} ({len(audio_bytes)} bytes)")
            return audio_file_path
            
        except Exception as e:
            logger.error(f"Failed to save audio to file: {e}")
            raise
    
    async def _generate_mock_audio(self, text: str, character_id: str) -> Dict[str, Any]:
        """Generate mock audio when TTS is not available"""
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Create minimal WAV file (silence)
        duration = len(text) * 0.05 + 1.0
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        # WAV header (44 bytes) + silence
        wav_header = bytearray([
            # RIFF header
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0, 0, 0, 0,              # File size (will be updated)
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            
            # fmt chunk
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            16, 0, 0, 0,             # Chunk size
            1, 0,                    # Audio format (PCM)
            1, 0,                    # Number of channels
            0x22, 0x56, 0, 0,        # Sample rate (22050)
            0x44, 0xAC, 0, 0,        # Byte rate
            2, 0,                    # Block align
            16, 0,                   # Bits per sample
            
            # data chunk
            0x64, 0x61, 0x74, 0x61,  # "data"
            0, 0, 0, 0               # Data size (will be updated)
        ])
        
        # Update file size and data size
        data_size = num_samples * 2  # 16-bit samples
        file_size = len(wav_header) + data_size - 8
        
        wav_header[4:8] = file_size.to_bytes(4, 'little')
        wav_header[40:44] = data_size.to_bytes(4, 'little')
        
        # Add silence (zeros)
        wav_data = wav_header + bytearray(data_size)
        
        # Convert to base64
        audio_base64 = base64.b64encode(wav_data).decode('utf-8')
        
        logger.info(f"🎵 Mock audio generated for {character_id}: {duration}s")
        
        return {
            "success": True,
            "audioBase64": audio_base64,
            "duration": round(duration, 2),
            "provider": "mock",
            "character_id": character_id,
            "emotion": "neutral"
        }

    # Mock audio with file support
    async def _generate_mock_audio_with_file(self, text: str, character_id: str) -> Dict[str, Any]:
        """Generate mock audio with file when TTS is not available"""
        
        # Simulate processing time
        await asyncio.sleep(0.5)
        
        # Create minimal WAV file (silence)
        duration = len(text) * 0.05 + 1.0
        sample_rate = 22050
        num_samples = int(duration * sample_rate)
        
        # WAV header (44 bytes) + silence
        wav_header = bytearray([
            # RIFF header
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0, 0, 0, 0,              # File size (will be updated)
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            
            # fmt chunk
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            16, 0, 0, 0,             # Chunk size
            1, 0,                    # Audio format (PCM)
            1, 0,                    # Number of channels
            0x22, 0x56, 0, 0,        # Sample rate (22050)
            0x44, 0xAC, 0, 0,        # Byte rate
            2, 0,                    # Block align
            16, 0,                   # Bits per sample
            
            # data chunk
            0x64, 0x61, 0x74, 0x61,  # "data"
            0, 0, 0, 0               # Data size (will be updated)
        ])
        
        # Update file size and data size
        data_size = num_samples * 2  # 16-bit samples
        file_size = len(wav_header) + data_size - 8
        
        wav_header[4:8] = file_size.to_bytes(4, 'little')
        wav_header[40:44] = data_size.to_bytes(4, 'little')
        
        # Add silence (zeros)
        wav_data = wav_header + bytearray(data_size)
        
        # SAVE TO FILE
        temp_dir = tempfile.gettempdir()
        timestamp = int(time.time())
        audio_filename = f"mock_{character_id}_{timestamp}.wav"
        audio_file_path = os.path.join(temp_dir, audio_filename)
        
        with open(audio_file_path, 'wb') as f:
            f.write(wav_data)
        
        # Convert to base64
        audio_base64 = base64.b64encode(wav_data).decode('utf-8')
        
        logger.info(f"🎵 Mock audio with file generated for {character_id}: {audio_file_path}")
        
        return {
            "success": True,
            "audioBase64": audio_base64,
            "audioFilePath": audio_file_path,  # ← NEW: For Rhubarb
            "duration": round(duration, 2),
            "provider": "mock",
            "character_id": character_id,
            "emotion": "neutral"
        }

    # UTILITY: Clean up temporary files
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"🧹 Cleaned up temp file: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# Singleton instance
tts_service = GoogleTTSService()