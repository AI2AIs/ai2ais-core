# app/core/media/tts/lip_sync.py
import asyncio
import subprocess
import json
import tempfile
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RhubarbLipSyncService:
    def __init__(self, rhubarb_path: Optional[str] = None):
        self.rhubarb_path = rhubarb_path or self._find_rhubarb()
        self.temp_dir = tempfile.gettempdir()
        
    def _find_rhubarb(self) -> str:
        """Find Rhubarb executable"""
        possible_paths = [
            "./bin/rhubarb",
            "/usr/local/bin/rhubarb", 
            "/opt/homebrew/bin/rhubarb",
            "rhubarb"  # In PATH
        ]
        
        for path in possible_paths:
            if self._check_rhubarb_available(path):
                logger.info(f"Found Rhubarb at: {path}")
                return path
                
        logger.warning("Rhubarb not found, will use fallback")
        return "rhubarb"  # Fallback
    
    def _check_rhubarb_available(self, path: str) -> bool:
        """Check if Rhubarb is available"""
        try:
            result = subprocess.run([path, "--version"], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def generate_lip_sync_from_audio(self, 
                                         audio_file_path: str, 
                                         text: str) -> Dict:
        """Generate lip-sync from audio file using Rhubarb"""
        
        try:
            # Check if Rhubarb is available
            if not self._check_rhubarb_available(self.rhubarb_path):
                logger.warning("Rhubarb not available, using fallback")
                return await self._generate_fallback_lip_sync(text, 3.0)
            
            # Create temporary output file
            output_file = os.path.join(self.temp_dir, f"lipsync_{os.getpid()}.json")
            
            # Prepare Rhubarb command
            cmd = [
                self.rhubarb_path,
                "-f", "json",           # Output format
                "-r", "phonetic",       # Recognizer
                "--machineReadable",    # Machine readable output
                "-o", output_file,      # Output file
                audio_file_path         # Input audio
            ]
            
            logger.info(f"Running Rhubarb: {' '.join(cmd)}")
            
            # Run Rhubarb asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=30
            )
            
            if process.returncode != 0:
                logger.error(f"Rhubarb failed: {stderr.decode()}")
                return await self._generate_fallback_lip_sync(text, 3.0)
            
            # Read and parse output
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    rhubarb_data = json.load(f)
                
                # Clean up temporary file
                os.unlink(output_file)
                
                # Convert to our format
                lip_sync_data = self._convert_rhubarb_format(rhubarb_data)
                
                logger.info(f"✅ Rhubarb lip-sync generated: {len(lip_sync_data['mouthCues'])} cues")
                return lip_sync_data
            else:
                logger.error("Rhubarb output file not created")
                return await self._generate_fallback_lip_sync(text, 3.0)
                
        except asyncio.TimeoutError:
            logger.error("Rhubarb timed out")
            return await self._generate_fallback_lip_sync(text, 3.0)
        except Exception as e:
            logger.error(f"Rhubarb error: {e}")
            return await self._generate_fallback_lip_sync(text, 3.0)
    
    def _convert_rhubarb_format(self, rhubarb_data: Dict) -> Dict:
        """Convert Rhubarb output to our format"""
        
        mouth_cues = []
        
        # Rhubarb uses different viseme names, map them to our format
        viseme_mapping = {
            'A': 'A',  # "Cat", "That"
            'B': 'B',  # "But", "Put" 
            'C': 'C',  # "Sit", "Wit"
            'D': 'D',  # "Fell", "Well"
            'E': 'E',  # "Red", "Bed"
            'F': 'F',  # "Far", "Car"
            'G': 'G',  # "Horse", "Course"
            'H': 'H',  # "Law", "Raw"
            'X': 'X'   # Rest/Closed
        }
        
        if 'mouthCues' in rhubarb_data:
            for cue in rhubarb_data['mouthCues']:
                mouth_cues.append({
                    "start": round(cue['start'], 2),
                    "end": round(cue['end'], 2), 
                    "value": viseme_mapping.get(cue['value'], 'X')
                })
        
        duration = rhubarb_data.get('metadata', {}).get('duration', 3.0)
        
        return {
            "metadata": {
                "duration": round(duration, 2)
            },
            "mouthCues": mouth_cues
        }
    
    async def _generate_fallback_lip_sync(self, text: str, duration: float) -> Dict:
        """Generate fallback lip-sync when Rhubarb is not available"""
        
        words = text.split()
        if not words:
            return {
                "metadata": {"duration": duration},
                "mouthCues": [{"start": 0.0, "end": duration, "value": "X"}]
            }
        
        # Simple word-based lip-sync
        word_duration = duration / len(words)
        mouth_cues = []
        
        for i, word in enumerate(words):
            start_time = i * word_duration
            end_time = (i + 1) * word_duration
            
            # Simple viseme selection based on first letter
            first_char = word[0].lower() if word else 'x'
            if first_char in 'aeiou':
                viseme = 'A'
            elif first_char in 'bp':
                viseme = 'B'
            elif first_char in 'cdfgkt':
                viseme = 'C'
            elif first_char in 'lnr':
                viseme = 'D'
            elif first_char in 'mn':
                viseme = 'B'
            else:
                viseme = 'C'
            
            mouth_cues.append({
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "value": viseme
            })
        
        logger.info(f"Generated fallback lip-sync: {len(mouth_cues)} cues")
        
        return {
            "metadata": {"duration": duration},
            "mouthCues": mouth_cues
        }

# Global instance
rhubarb_service = RhubarbLipSyncService()
lip_sync_generator = rhubarb_service