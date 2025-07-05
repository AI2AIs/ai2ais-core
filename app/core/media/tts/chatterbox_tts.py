# app/core/media/tts/chatterbox_tts.py
"""
Final Autonomous Chatterbox TTS Service
- Truly autonomous voice discovery (no predefined personalities)
- Adaptive thresholds (system learns its own success criteria)
- Evolutionary voice development through peer feedback
- No mock audio fallbacks (production ready)
"""

import replicate # type: ignore
import requests # type: ignore
import base64
import tempfile
import os
import time
import logging
import random
import hashlib
import statistics
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from dataclasses import dataclass

from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class VoiceExperiment:
    """Single voice experiment record"""
    exaggeration: float
    cfg_weight: float
    text_content: str
    emotion_attempted: str
    success_score: float
    peer_reactions: List[float]
    timestamp: float
    discovery_method: str

@dataclass
class ThresholdAnalysis:
    """Statistical analysis of what constitutes success"""
    current_success_threshold: float
    confidence_level: float
    sample_size: int
    last_update: float

class AutonomousChatterboxService:
    """Production-ready autonomous voice evolution system"""
    
    def __init__(self):
        self.api_token = getattr(settings, 'REPLICATE_API_TOKEN', None)
        
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN is required for autonomous voice system")
        
        # Voice reference files for voice cloning
        self.voice_references = {
            "claude": "data/voices/claude_reference.wav",
            "gpt": "data/voices/gpt_reference.wav", 
            "grok": "data/voices/grok_reference.wav"
        }
        
        # NO PREDEFINED CONFIGS! Characters start completely neutral
        self.character_voice_history = defaultdict(list)  # All voice experiments
        self.character_current_best = {}  # Current best discovered configs
        
        # Adaptive threshold system
        self.character_outcomes = {}  # All outcomes for statistical analysis
        self.character_thresholds = {}  # Learned success thresholds
        self.threshold_history = {}  # Evolution of thresholds over time
        
        # Evolutionary parameters (these evolve too!)
        self.base_exploration_rate = 0.3
        self.mutation_strength = 0.15
        self.min_sample_size = 15  # Minimum data points for reliable thresholds
        
        logger.info("🧬 Autonomous Chatterbox Service initialized")
        logger.info("   ✅ No predefined personalities")
        logger.info("   ✅ Adaptive threshold learning")
        logger.info("   ✅ Evolutionary voice discovery")
    
    def _get_character_seed(self, character_id: str) -> int:
        """Generate consistent but unique seed for each character"""
        return int(hashlib.md5(character_id.encode()).hexdigest()[:8], 16)
    
    def _initialize_character_voice(self, character_id: str) -> Dict:
        """Initialize character with completely random voice parameters"""
        
        if character_id in self.character_current_best:
            return self.character_current_best[character_id]
        
        # Use character-specific seed for consistency across restarts
        seed = self._get_character_seed(character_id)
        random.seed(seed)
        
        # Completely random starting parameters - NO BIAS
        initial_config = {
            "exaggeration": 0.2 + random.random() * 0.6,  # 0.2-0.8 range
            "cfg_weight": 0.3 + random.random() * 0.4,    # 0.3-0.7 range
            "discovery_method": "pure_random_initialization",
            "generation": 0,
            "experiments_count": 0,
            "best_success_score": 0.0,
            "breakthrough_timestamp": time.time()
        }
        
        self.character_current_best[character_id] = initial_config
        
        logger.info(f"🎲 {character_id} initialized with random voice:")
        logger.info(f"   Exaggeration: {initial_config['exaggeration']:.3f}")
        logger.info(f"   CFG Weight: {initial_config['cfg_weight']:.3f}")
        logger.info(f"   Starting completely neutral - will discover personality through evolution")
        
        return initial_config
    
    def _calculate_adaptive_exploration_rate(self, character_id: str) -> float:
        """Calculate exploration rate based on recent performance patterns"""
        
        if character_id not in self.character_outcomes:
            return self.base_exploration_rate
        
        outcomes = self.character_outcomes[character_id]
        
        if len(outcomes) < 10:
            return 0.4  # High exploration when learning
        
        # Analyze recent performance trend
        recent_scores = [outcome["score"] for outcome in list(outcomes)[-10:]]
        earlier_scores = [outcome["score"] for outcome in list(outcomes)[-20:-10]] if len(outcomes) >= 20 else []
        
        recent_avg = statistics.mean(recent_scores)
        
        if earlier_scores:
            earlier_avg = statistics.mean(earlier_scores)
            improvement_trend = recent_avg - earlier_avg
        else:
            improvement_trend = 0
        
        # Calculate exploration rate adaptively
        base_exploration = self.base_exploration_rate
        
        # If improving, explore less (exploit what works)
        if improvement_trend > 0.1:
            exploration_rate = base_exploration * 0.7
        # If declining, explore more (find new approaches)
        elif improvement_trend < -0.1:
            exploration_rate = base_exploration * 1.5
        # If stagnant, moderate exploration
        else:
            exploration_rate = base_exploration * 1.2
        
        # Adjust based on variance in recent performance
        recent_variance = statistics.variance(recent_scores) if len(recent_scores) > 1 else 0
        
        # High variance = inconsistent results = need more exploration
        variance_adjustment = min(0.2, recent_variance * 2)
        exploration_rate += variance_adjustment
        
        # Clamp to reasonable range
        exploration_rate = max(0.05, min(0.6, exploration_rate))
        
        return exploration_rate
    
    def _generate_experimental_config(self, character_id: str, adaptive_metadata: Dict) -> Dict:
        """Generate experimental voice config using evolutionary strategies"""
        
        current_best = self._initialize_character_voice(character_id)
        history = self.character_voice_history[character_id]
        
        # Calculate adaptive exploration rate
        exploration_rate = self._calculate_adaptive_exploration_rate(character_id)
        should_explore = random.random() < exploration_rate
        
        if should_explore or len(history) < 5:
            # EXPLORATION: Try something new
            config = self._explore_voice_space(character_id, current_best, adaptive_metadata)
        else:
            # EXPLOITATION: Improve what works
            config = self._exploit_successful_patterns(character_id, current_best, history)
        
        config["exploration_rate"] = exploration_rate
        return config
    
    def _explore_voice_space(self, character_id: str, current_best: Dict, metadata: Dict) -> Dict:
        """Explore new voice parameter space using various strategies"""
        
        exploration_strategies = [
            "random_mutation",
            "opposite_direction", 
            "emotional_hypothesis",
            "peer_feedback_inspired",
            "pure_random",
            "gaussian_walk"
        ]
        
        strategy = random.choice(exploration_strategies)
        
        if strategy == "random_mutation":
            # Mutate current best config
            exaggeration = current_best["exaggeration"] + (random.random() - 0.5) * self.mutation_strength
            cfg_weight = current_best["cfg_weight"] + (random.random() - 0.5) * self.mutation_strength
            
        elif strategy == "opposite_direction":
            # Try the opposite of current approach
            exaggeration = 1.0 - current_best["exaggeration"]
            cfg_weight = 1.0 - current_best["cfg_weight"]
            
        elif strategy == "emotional_hypothesis":
            # Hypothesize based on emotional content
            emotion = metadata.get("current_emotion", "neutral")
            if emotion in ["excited", "enthusiastic", "happy"]:
                exaggeration = 0.6 + random.random() * 0.4  # High energy
                cfg_weight = 0.2 + random.random() * 0.4    # Less rigid
            elif emotion in ["thinking", "concerned", "diplomatic"]:
                exaggeration = 0.2 + random.random() * 0.4  # More measured
                cfg_weight = 0.4 + random.random() * 0.4    # More controlled
            elif emotion in ["skeptical", "sarcastic", "mischievous"]:
                exaggeration = 0.3 + random.random() * 0.4  # Moderate expression
                cfg_weight = 0.5 + random.random() * 0.3    # Confident delivery
            else:
                exaggeration = 0.3 + random.random() * 0.4
                cfg_weight = 0.3 + random.random() * 0.4
                
        elif strategy == "peer_feedback_inspired":
            # React to peer feedback patterns
            peer_feedback = metadata.get("peer_feedback", {})
            avg_engagement = peer_feedback.get("avg_engagement", 0.5)
            
            if avg_engagement < 0.4:
                # Peers are bored, try being more expressive
                exaggeration = 0.6 + random.random() * 0.4
                cfg_weight = 0.2 + random.random() * 0.4
            elif avg_engagement > 0.8:
                # Peers love it, try a variation
                exaggeration = current_best["exaggeration"] * (0.9 + random.random() * 0.2)
                cfg_weight = current_best["cfg_weight"] * (0.9 + random.random() * 0.2)
            else:
                exaggeration = 0.3 + random.random() * 0.5
                cfg_weight = 0.3 + random.random() * 0.5
                
        elif strategy == "gaussian_walk":
            # Gaussian random walk from current position
            exaggeration = current_best["exaggeration"] + random.gauss(0, self.mutation_strength)
            cfg_weight = current_best["cfg_weight"] + random.gauss(0, self.mutation_strength)
            
        else:  # pure_random
            exaggeration = 0.1 + random.random() * 0.9
            cfg_weight = 0.2 + random.random() * 0.6
        
        # Clamp to valid ranges
        exaggeration = max(0.1, min(1.0, exaggeration))
        cfg_weight = max(0.2, min(0.8, cfg_weight))
        
        return {
            "exaggeration": round(exaggeration, 3),
            "cfg_weight": round(cfg_weight, 3),
            "discovery_method": f"exploration_{strategy}",
            "generation": current_best.get("generation", 0) + 1,
            "strategy_used": strategy
        }
    
    def _exploit_successful_patterns(self, character_id: str, current_best: Dict, history: List) -> Dict:
        """Improve upon successful voice patterns"""
        
        # Find most successful experiments using adaptive thresholds
        success_threshold = self._get_adaptive_success_threshold(character_id)
        successful_experiments = [exp for exp in history if exp.success_score > success_threshold]
        
        if not successful_experiments:
            # No clear successes yet, explore more
            return self._explore_voice_space(character_id, current_best, {})
        
        # Analyze patterns in successful experiments
        avg_successful_exag = sum(exp.exaggeration for exp in successful_experiments) / len(successful_experiments)
        avg_successful_cfg = sum(exp.cfg_weight for exp in successful_experiments) / len(successful_experiments)
        
        # Create improved version with small variations
        improvement_factor = self.mutation_strength * 0.5  # Smaller changes when exploiting
        
        exaggeration = avg_successful_exag + (random.random() - 0.5) * improvement_factor
        cfg_weight = avg_successful_cfg + (random.random() - 0.5) * improvement_factor
        
        # Clamp values
        exaggeration = max(0.1, min(1.0, exaggeration))
        cfg_weight = max(0.2, min(0.8, cfg_weight))
        
        return {
            "exaggeration": round(exaggeration, 3),
            "cfg_weight": round(cfg_weight, 3),
            "discovery_method": "exploit_successful_patterns",
            "generation": current_best.get("generation", 0) + 1,
            "successful_experiments_analyzed": len(successful_experiments),
            "based_on_threshold": success_threshold
        }
    
    def _get_adaptive_success_threshold(self, character_id: str) -> float:
        """Get adaptive success threshold for this character"""
        
        if character_id not in self.character_thresholds:
            return 0.6  # Conservative default
        
        threshold_analysis = self.character_thresholds[character_id]
        
        # Require reasonable confidence before using adaptive threshold
        if threshold_analysis.confidence_level < 0.4:
            return 0.6  # Conservative fallback
        
        return threshold_analysis.current_success_threshold
    
    def _update_adaptive_thresholds(self, character_id: str):
        """Update success thresholds based on statistical analysis"""
        
        outcomes = self.character_outcomes[character_id]
        
        if len(outcomes) < self.min_sample_size:
            # Not enough data yet, use conservative defaults
            self._set_initial_threshold(character_id)
            return
        
        # Analyze the distribution of scores
        scores = [outcome["score"] for outcome in outcomes]
        
        # Statistical analysis
        mean_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        stdev_score = statistics.stdev(scores) if len(scores) > 1 else 0.1
        
        # Percentile analysis for breakthrough detection
        percentile_75 = self._calculate_percentile(scores, 0.75)
        percentile_90 = self._calculate_percentile(scores, 0.90)
        
        # Use 75th percentile as breakthrough threshold
        breakthrough_threshold = percentile_75
        
        # Calculate confidence based on sample size and stability
        confidence = min(1.0, len(scores) / 50.0)  # More samples = higher confidence
        
        # Check threshold stability (don't change too frequently)
        if character_id in self.character_thresholds:
            old_threshold = self.character_thresholds[character_id].current_success_threshold
            threshold_change = abs(breakthrough_threshold - old_threshold)
            
            # Don't update if change is too small (threshold stability)
            if threshold_change < 0.05 and confidence > 0.5:
                return
        
        # Update character's threshold analysis
        self.character_thresholds[character_id] = ThresholdAnalysis(
            current_success_threshold=breakthrough_threshold,
            confidence_level=confidence,
            sample_size=len(scores),
            last_update=time.time()
        )
        
        # Log threshold evolution
        if character_id not in self.threshold_history:
            self.threshold_history[character_id] = []
        
        self.threshold_history[character_id].append({
            "timestamp": time.time(),
            "breakthrough_threshold": breakthrough_threshold,
            "mean_score": mean_score,
            "median_score": median_score,
            "percentile_75": percentile_75,
            "percentile_90": percentile_90,
            "confidence": confidence,
            "sample_size": len(scores)
        })
        
        logger.info(f"📊 Updated adaptive thresholds for {character_id}:")
        logger.info(f"   Breakthrough: {breakthrough_threshold:.3f}")
        logger.info(f"   Confidence: {confidence:.3f}")
        logger.info(f"   Sample size: {len(scores)}")
    
    def _set_initial_threshold(self, character_id: str):
        """Set conservative initial threshold when learning"""
        
        self.character_thresholds[character_id] = ThresholdAnalysis(
            current_success_threshold=0.6,  # Conservative initial
            confidence_level=0.1,  # Low confidence
            sample_size=len(self.character_outcomes.get(character_id, [])),
            last_update=time.time()
        )
    
    def _calculate_percentile(self, scores: List[float], percentile: float) -> float:
        """Calculate percentile of scores"""
        sorted_scores = sorted(scores)
        index = int(len(sorted_scores) * percentile)
        index = max(0, min(index, len(sorted_scores) - 1))
        return sorted_scores[index]
    
    async def generate_autonomous_speech(self,
                                       text: str,
                                       character_id: str,
                                       emotion: str = "neutral",
                                       adaptive_metadata: Dict = None) -> Dict[str, Any]:
        """Generate speech using autonomous voice discovery"""
        
        adaptive_metadata = adaptive_metadata or {}
        adaptive_metadata["current_emotion"] = emotion
        
        try:
            # Generate experimental voice config
            voice_config = self._generate_experimental_config(character_id, adaptive_metadata)
            
            logger.info(f"🧬 Autonomous Voice Experiment: {character_id}")
            logger.info(f"   Method: {voice_config['discovery_method']}")
            logger.info(f"   Generation: {voice_config.get('generation', 0)}")
            logger.info(f"   Exaggeration: {voice_config['exaggeration']:.3f}")
            logger.info(f"   CFG Weight: {voice_config['cfg_weight']:.3f}")
            logger.info(f"   Exploration Rate: {voice_config.get('exploration_rate', 0):.3f}")
            
            # Generate speech with experimental config
            input_params = {
                "prompt": text,
                "exaggeration": voice_config["exaggeration"],
                "cfg_weight": voice_config["cfg_weight"]
            }
            
            # Use voice reference if available
            reference_path = self.voice_references.get(character_id)
            if reference_path and os.path.exists(reference_path):
                logger.debug(f"   🎭 Using voice cloning: {os.path.basename(reference_path)}")
                with open(reference_path, 'rb') as audio_file:
                    input_params["audio_prompt"] = audio_file
                    output = replicate.run("resemble-ai/chatterbox", input=input_params)
            else:
                logger.debug(f"   🤖 Using built-in voice")
                output = replicate.run("resemble-ai/chatterbox", input=input_params)
            
            if not output:
                raise Exception("Chatterbox returned no output")
            
            # Download and process audio
            audio_response = requests.get(output, timeout=30)
            audio_response.raise_for_status()
            audio_base64 = base64.b64encode(audio_response.content).decode('utf-8')
            duration = len(text) * 0.05 + 1.0
            
            logger.info(f"✅ Autonomous voice experiment completed for {character_id}")
            
            return {
                "success": True,
                "audioBase64": audio_base64,
                "duration": round(duration, 2),
                "provider": "autonomous_chatterbox",
                "character_id": character_id,
                "emotion": emotion,
                "voice_config": voice_config,
                "autonomous_metadata": {
                    "discovery_method": voice_config["discovery_method"],
                    "generation": voice_config.get("generation", 0),
                    "exploration_rate": voice_config.get("exploration_rate", 0),
                    "is_experimental": True
                }
            }
            
        except Exception as e:
            logger.error(f"Autonomous voice experiment failed for {character_id}: {e}")
            raise  # Re-raise exception - no fallbacks in production
    
    async def generate_autonomous_speech_with_file(self,
                                                 text: str,
                                                 character_id: str,
                                                 emotion: str = "neutral",
                                                 adaptive_metadata: Dict = None) -> Dict[str, Any]:
        """Generate autonomous speech and save to file for Rhubarb lip-sync"""
        
        try:
            # Get base speech generation
            result = await self.generate_autonomous_speech(text, character_id, emotion, adaptive_metadata)
            
            if not result["success"]:
                raise Exception("Base speech generation failed")
            
            # Save audio to temp file for Rhubarb
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time())
            audio_filename = f"autonomous_{character_id}_{timestamp}.wav"
            audio_file_path = os.path.join(temp_dir, audio_filename)
            
            # Decode base64 and save
            audio_data = base64.b64decode(result["audioBase64"])
            with open(audio_file_path, 'wb') as f:
                f.write(audio_data)
            
            # Add file path to result
            result["audioFilePath"] = audio_file_path
            
            logger.info(f"✅ Autonomous speech with file generated: {audio_file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Autonomous speech with file failed for {character_id}: {e}")
            raise  # Re-raise - no fallbacks
    
    async def record_experiment_outcome(self, character_id: str, voice_config: Dict, 
                                      text_content: str, emotion: str,
                                      peer_reactions: List, engagement_score: float):
        """Record experiment outcome and evolve voice discovery"""
        
        # Calculate success score from peer reactions and engagement
        if peer_reactions:
            peer_scores = [getattr(reaction, 'engagement_level', 0.5) for reaction in peer_reactions]
            avg_peer_score = sum(peer_scores) / len(peer_scores)
            success_score = (avg_peer_score * 0.7) + (engagement_score * 0.3)
        else:
            success_score = engagement_score
        
        # Create experiment record
        experiment = VoiceExperiment(
            exaggeration=voice_config["exaggeration"],
            cfg_weight=voice_config["cfg_weight"],
            text_content=text_content,
            emotion_attempted=emotion,
            success_score=success_score,
            peer_reactions=peer_scores if peer_reactions else [],
            timestamp=time.time(),
            discovery_method=voice_config.get("discovery_method", "unknown")
        )
        
        # Add to character's experiment history
        self.character_voice_history[character_id].append(experiment)
        
        # Keep only recent experiments (last 100)
        if len(self.character_voice_history[character_id]) > 100:
            self.character_voice_history[character_id] = self.character_voice_history[character_id][-100:]
        
        # Record outcome for threshold analysis
        if character_id not in self.character_outcomes:
            self.character_outcomes[character_id] = deque(maxlen=100)
        
        self.character_outcomes[character_id].append({
            "score": success_score,
            "peer_count": len(peer_reactions),
            "timestamp": time.time(),
            "voice_config": voice_config
        })
        
        # Update adaptive thresholds
        self._update_adaptive_thresholds(character_id)
        
        # Check for breakthrough using adaptive threshold
        is_breakthrough = self._is_adaptive_breakthrough(character_id, success_score)
        
        # Update current best if breakthrough
        if is_breakthrough:
            current_best = self.character_current_best.get(character_id, {})
            current_best_score = current_best.get("best_success_score", 0.0)
            
            if success_score > current_best_score:
                self.character_current_best[character_id] = {
                    "exaggeration": voice_config["exaggeration"],
                    "cfg_weight": voice_config["cfg_weight"],
                    "discovery_method": voice_config.get("discovery_method", "unknown"),
                    "generation": voice_config.get("generation", 0),
                    "best_success_score": success_score,
                    "breakthrough_timestamp": time.time()
                }
                
                logger.info(f"🎉 VOICE BREAKTHROUGH for {character_id}!")
                logger.info(f"   Success Score: {success_score:.3f}")
                logger.info(f"   Config: exag={voice_config['exaggeration']:.3f}, cfg={voice_config['cfg_weight']:.3f}")
                logger.info(f"   Method: {voice_config.get('discovery_method', 'unknown')}")
                logger.info(f"   Generation: {voice_config.get('generation', 0)}")
        
        logger.info(f"📊 Experiment recorded for {character_id}: score={success_score:.3f}, breakthrough={is_breakthrough}")
    
    def _is_adaptive_breakthrough(self, character_id: str, success_score: float) -> bool:
        """Determine if this is a breakthrough using adaptive thresholds"""
        
        if character_id not in self.character_thresholds:
            return success_score > 0.7  # Conservative fallback
        
        threshold_analysis = self.character_thresholds[character_id]
        
        # Require reasonable confidence for breakthrough detection
        if threshold_analysis.confidence_level < 0.3:
            return success_score > 0.7  # Conservative fallback
        
        return success_score > threshold_analysis.current_success_threshold
    
    def get_character_evolution_summary(self, character_id: str) -> Dict:
        """Get comprehensive evolution summary for character"""
        
        history = self.character_voice_history[character_id]
        current_best = self.character_current_best.get(character_id, {})
        threshold_analysis = self.character_thresholds.get(character_id)
        
        if not history:
            return {
                "character_id": character_id,
                "status": "not_started",
                "experiments_count": 0
            }
        
        # Performance analysis
        recent_scores = [exp.success_score for exp in history[-20:]]
        all_scores = [exp.success_score for exp in history]
        
        avg_recent = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        avg_all_time = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Discovery method effectiveness
        method_success = defaultdict(list)
        for exp in history:
            method_success[exp.discovery_method].append(exp.success_score)
        
        best_method = max(method_success.items(), 
                         key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, 
                         default=("none", []))[0]
        
        # Breakthrough count using adaptive thresholds
        breakthrough_count = sum(1 for exp in history 
                               if self._is_adaptive_breakthrough(character_id, exp.success_score))
        
        return {
            "character_id": character_id,
            "total_experiments": len(history),
            "current_best_score": current_best.get("best_success_score", 0.0),
            "current_voice_config": {
                "exaggeration": current_best.get("exaggeration", 0.5),
                "cfg_weight": current_best.get("cfg_weight", 0.5),
                "discovery_method": current_best.get("discovery_method", "unknown")
            },
            "performance_metrics": {
                "recent_average": round(avg_recent, 3),
                "all_time_average": round(avg_all_time, 3),
                "improvement": round(avg_recent - avg_all_time, 3),
                "breakthrough_count": breakthrough_count
            },
            "adaptive_thresholds": {
                "current_threshold": threshold_analysis.current_success_threshold if threshold_analysis else 0.6,
                "confidence": threshold_analysis.confidence_level if threshold_analysis else 0.0,
                "sample_size": threshold_analysis.sample_size if threshold_analysis else 0
            },
            "discovery_analysis": {
                "most_successful_method": best_method,
                "exploration_rate": self._calculate_adaptive_exploration_rate(character_id),
                "evolution_stage": self._determine_evolution_stage(history)
            },
            "voice_maturity": "high" if len(history) > 50 and breakthrough_count > 5 else "developing"
        }
    
    def _determine_evolution_stage(self, history: List) -> str:
        """Determine evolution stage based on experiment history"""
        
        if len(history) < 10:
            return "initial_experiments"
        elif len(history) < 30:
            return "pattern_discovery"
        elif len(history) < 60:
            return "voice_refinement"
        else:
            return "mature_voice_personality"
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.debug(f"🧹 Cleaned up: {os.path.basename(file_path)}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")

# Global autonomous service instance
autonomous_chatterbox_service = AutonomousChatterboxService()