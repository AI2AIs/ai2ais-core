# app/core/database/service.py
"""
A2AIs Database Service Layer
PostgreSQL operations with robust error handling and connection management
"""

import asyncio
import asyncpg
import logging
import json
import uuid
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from enum import Enum

from app.config.settings import settings

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base database error"""
    pass

class ConnectionError(DatabaseError):
    """Database connection error"""
    pass

class ValidationError(DatabaseError):
    """Data validation error"""
    pass

class ServiceState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    SHUTDOWN = "shutdown"

class DatabaseService:
    """PostgreSQL service for A2AIs character persistence - FULLY ROBUST"""
    
    def __init__(self):
        self.db_url = settings.DATABASE_URL
        self.pool: Optional[asyncpg.Pool] = None
        self._connected = False
        self.state = ServiceState.UNINITIALIZED
        
        # Thread safety
        self._connection_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        
        # Performance tracking
        self._query_count = 0
        self._error_count = 0
        self._last_health_check = None
        
        # Valid database fields for security
        self._valid_personality_traits = {
            'analytical_score', 'creative_score', 'assertive_score', 
            'empathetic_score', 'skeptical_score'
        }
        
        self._valid_evolution_stages = {
            'initial_learning', 'pattern_recognition', 
            'personality_formation', 'mature_adaptation'
        }
    
    # ==========================================
    # CONNECTION MANAGEMENT - ROBUST
    # ==========================================
    
    async def initialize(self):
        """Thread-safe initialization with comprehensive error handling"""
        if self.state in [ServiceState.READY, ServiceState.INITIALIZING]:
            return
            
        async with self._connection_lock:
            if self.state == ServiceState.READY:
                return
            
            if self.state == ServiceState.SHUTDOWN:
                raise ConnectionError("Service is shut down")
            
            self.state = ServiceState.INITIALIZING
            
            try:
                logger.info("🔄 Initializing database connection pool...")
                
                # Create connection pool with robust settings
                self.pool = await asyncpg.create_pool(
                    self.db_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'a2ais_core',
                        'timezone': 'UTC',
                        'statement_timeout': '30s'
                    },
                    setup=self._setup_connection
                )
                
                # Test connection with timeout
                await asyncio.wait_for(self._test_connection(), timeout=10.0)
                
                self.state = ServiceState.READY
                logger.info("✅ Database connection pool initialized successfully")
                
            except asyncio.TimeoutError:
                logger.error("❌ Database initialization timeout")
                await self._cleanup_failed_initialization()
                raise ConnectionError("Database initialization timeout")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize database: {e}")
                await self._cleanup_failed_initialization()
                raise ConnectionError(f"Database initialization failed: {e}")
    
    async def _setup_connection(self, conn: asyncpg.Connection):
        """Setup individual connection"""
        await conn.execute("SET timezone = 'UTC'")
        # Add any other per-connection setup here
    
    async def _test_connection(self):
        """Test database connection"""
        if not self.pool:
            raise ConnectionError("Pool not initialized")
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise ConnectionError("Connection test failed")
    
    async def _cleanup_failed_initialization(self):
        """Cleanup after failed initialization"""
        if self.pool:
            try:
                await self.pool.close()
            except:
                pass
            finally:
                self.pool = None
        
        self.state = ServiceState.UNINITIALIZED
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection with comprehensive error handling"""
        if self.state == ServiceState.SHUTDOWN:
            raise ConnectionError("Service is shut down")
        
        # Initialize if needed
        if self.state != ServiceState.READY:
            await self.initialize()
        
        if not self.pool:
            raise ConnectionError("Database pool not available")
        
        connection = None
        try:
            # Acquire connection with timeout
            connection = await asyncio.wait_for(
                self.pool.acquire(), 
                timeout=5.0
            )
            
            # Verify connection is healthy
            await connection.fetchval("SELECT 1")
            
            yield connection
            
        except asyncio.TimeoutError:
            logger.error("❌ Connection acquisition timeout")
            self._error_count += 1
            raise ConnectionError("Connection acquisition timeout")
            
        except asyncpg.exceptions.ConnectionDoesNotExistError:
            logger.warning("⚠️ Connection lost, attempting recovery")
            self.state = ServiceState.DEGRADED
            
            # Try to reinitialize
            try:
                await self.initialize()
                async with self.pool.acquire() as new_conn:
                    yield new_conn
            except Exception as e:
                raise ConnectionError(f"Connection recovery failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Database connection error: {e}")
            self._error_count += 1
            raise ConnectionError(f"Database connection failed: {e}")
            
        finally:
            if connection:
                try:
                    await self.pool.release(connection)
                except:
                    pass  # Connection already closed/invalid
    
    async def close(self):
        """Graceful shutdown with comprehensive cleanup"""
        logger.info("🔌 Starting database service shutdown...")
        
        # Prevent new operations
        self.state = ServiceState.SHUTDOWN
        self._shutdown_event.set()
        
        if not self.pool:
            logger.info("🔌 No pool to close")
            return
        
        try:
            # Wait for active connections with timeout
            await asyncio.wait_for(
                self._wait_for_active_connections(), 
                timeout=15.0
            )
            
            # Close pool
            await self.pool.close()
            logger.info("✅ Database pool closed successfully")
            
        except asyncio.TimeoutError:
            logger.warning("⚠️ Timeout waiting for connections, forcing close")
            try:
                await self.pool.close()
            except:
                pass
        
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
        
        finally:
            self.pool = None
            logger.info("🔌 Database service shutdown complete")
    
    async def _wait_for_active_connections(self):
        """Wait for active connections to finish"""
        if not self.pool:
            return
        
        for _ in range(100):  # Max 10 seconds
            try:
                if hasattr(self.pool, '_holders') and len(self.pool._holders) == 0:
                    break
                await asyncio.sleep(0.1)
            except:
                break
    
    # ==========================================
    # CHARACTER EVOLUTION - ROBUST OPERATIONS
    # ==========================================
    
    async def get_character(self, character_id: str) -> Optional[Dict]:
        """Get character evolution data with validation"""
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        try:
            async with self.get_connection() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM character_evolution WHERE character_id = $1",
                    character_id
                )
                
                self._query_count += 1
                
                if row:
                    result = dict(row)
                    # Convert datetime objects to ISO strings for JSON serialization
                    for key, value in result.items():
                        if isinstance(value, datetime):
                            result[key] = value.isoformat()
                    return result
                
                return None
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error getting character {character_id}: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to get character: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error getting character {character_id}: {e}")
            self._error_count += 1
            raise
    
    async def update_character_personality(self, 
                                         character_id: str, 
                                         personality_changes: Dict[str, float]) -> bool:
        """Update character personality with comprehensive validation"""
        
        # Input validation
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        if not personality_changes:
            logger.warning(f"No personality changes provided for {character_id}")
            return True
        
        # Validate and filter personality traits
        validated_changes = {}
        for trait, value in personality_changes.items():
            if trait not in self._valid_personality_traits:
                logger.warning(f"Invalid personality trait ignored: {trait}")
                continue
            
            try:
                float_value = float(value)
                if not (0.0 <= float_value <= 1.0):
                    logger.warning(f"Personality value out of range [0,1]: {trait}={value}")
                    continue
                validated_changes[trait] = float_value
            except (TypeError, ValueError):
                logger.warning(f"Invalid personality value: {trait}={value}")
                continue
        
        if not validated_changes:
            logger.warning(f"No valid personality changes for {character_id}")
            return False
        
        try:
            async with self.get_connection() as conn:
                # Build parameterized query safely
                set_clauses = [f"{trait} = ${i+1}" for i, trait in enumerate(validated_changes.keys())]
                values = list(validated_changes.values())
                
                sql = f"""
                    UPDATE character_evolution 
                    SET {', '.join(set_clauses)}, updated_at = ${len(values) + 1}
                    WHERE character_id = ${len(values) + 2}
                """
                
                values.extend([datetime.now(), character_id])
                
                result = await conn.execute(sql, *values)
                self._query_count += 1
                
                # Parse result properly
                rows_affected = self._parse_update_result(result)
                success = rows_affected > 0
                
                if success:
                    logger.info(f"✅ Updated personality for {character_id}: {validated_changes}")
                else:
                    logger.warning(f"⚠️ Character {character_id} not found for personality update")
                
                return success
                
        except asyncpg.exceptions.UniqueViolationError:
            logger.error(f"❌ Character {character_id} constraint violation")
            self._error_count += 1
            return False
            
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error updating personality: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to update personality: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error updating personality: {e}")
            self._error_count += 1
            raise
    
    async def update_character_evolution_stage(self, 
                                             character_id: str, 
                                             new_stage: str, 
                                             maturity_level: int = None) -> bool:
        """Update character evolution stage with validation"""
        
        # Validation
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        if new_stage not in self._valid_evolution_stages:
            raise ValidationError(f"Invalid evolution stage: {new_stage}")
        
        if maturity_level is not None and not (1 <= maturity_level <= 10):
            raise ValidationError(f"Invalid maturity level: {maturity_level}")
        
        try:
            async with self.get_connection() as conn:
                if maturity_level is not None:
                    result = await conn.execute("""
                        UPDATE character_evolution 
                        SET evolution_stage = $1, maturity_level = $2, updated_at = $3
                        WHERE character_id = $4
                    """, new_stage, maturity_level, datetime.now(), character_id)
                else:
                    result = await conn.execute("""
                        UPDATE character_evolution 
                        SET evolution_stage = $1, updated_at = $2
                        WHERE character_id = $3
                    """, new_stage, datetime.now(), character_id)
                
                self._query_count += 1
                rows_affected = self._parse_update_result(result)
                success = rows_affected > 0
                
                if success:
                    logger.info(f"✅ Updated evolution stage for {character_id}: {new_stage}")
                else:
                    logger.warning(f"⚠️ Character {character_id} not found for evolution update")
                
                return success
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error updating evolution stage: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to update evolution stage: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error updating evolution stage: {e}")
            self._error_count += 1
            raise
    
    async def increment_character_stats(self, 
                                      character_id: str, 
                                      sessions: int = 0, 
                                      speeches: int = 0, 
                                      breakthroughs: int = 0) -> bool:
        """Increment character statistics with validation"""
        
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        # Validate increments
        if not all(isinstance(x, int) and x >= 0 for x in [sessions, speeches, breakthroughs]):
            raise ValidationError("Stats increments must be non-negative integers")
        
        try:
            async with self.get_connection() as conn:
                result = await conn.execute("""
                    UPDATE character_evolution 
                    SET 
                        total_sessions = total_sessions + $1,
                        total_speeches = total_speeches + $2,
                        breakthrough_count = breakthrough_count + $3,
                        last_breakthrough_at = CASE 
                            WHEN $3 > 0 THEN $4
                            ELSE last_breakthrough_at 
                        END,
                        updated_at = $4
                    WHERE character_id = $5
                """, sessions, speeches, breakthroughs, datetime.now(), character_id)
                
                self._query_count += 1
                rows_affected = self._parse_update_result(result)
                success = rows_affected > 0
                
                if success:
                    logger.info(f"✅ Incremented stats for {character_id}: "
                              f"sessions=+{sessions}, speeches=+{speeches}, breakthroughs=+{breakthroughs}")
                else:
                    logger.warning(f"⚠️ Character {character_id} not found for stats update")
                
                return success
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error incrementing stats: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to increment stats: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error incrementing stats: {e}")
            self._error_count += 1
            raise
    
    # ==========================================
    # SURVIVAL MECHANICS - ROBUST
    # ==========================================
    
    async def update_character_energy(self, 
                                    character_id: str, 
                                    energy_delta: float, 
                                    event_type: str, 
                                    event_source: str = "manual") -> Optional[float]:
        """Update character life energy with validation"""
        
        # Validation
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        try:
            energy_delta = float(energy_delta)
            if not (-100.0 <= energy_delta <= 100.0):
                raise ValidationError(f"Energy delta out of range: {energy_delta}")
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid energy delta: {energy_delta}")
        
        if not event_type or not isinstance(event_type, str):
            raise ValidationError(f"Invalid event_type: {event_type}")
        
        try:
            async with self.get_connection() as conn:
                # Use stored procedure if available, fallback to manual update
                try:
                    new_energy = await conn.fetchval("""
                        SELECT update_character_energy($1, $2, $3, $4)
                    """, character_id, energy_delta, event_type, event_source)
                    
                    self._query_count += 1
                    return float(new_energy) if new_energy is not None else None
                    
                except asyncpg.exceptions.UndefinedFunctionError:
                    # Fallback to manual update if stored procedure doesn't exist
                    logger.warning("Stored procedure not found, using manual energy update")
                    return await self._manual_energy_update(conn, character_id, energy_delta, event_type, event_source)
                    
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error updating energy: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to update energy: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error updating energy: {e}")
            self._error_count += 1
            raise
    
    async def _manual_energy_update(self, conn, character_id: str, energy_delta: float, 
                                   event_type: str, event_source: str) -> Optional[float]:
        """Manual energy update fallback"""
        async with conn.transaction():
            # Update energy
            result = await conn.fetchrow("""
                UPDATE character_evolution 
                SET 
                    life_energy = GREATEST(0, LEAST(100, life_energy + $1)),
                    last_energy_update = $2,
                    updated_at = $2
                WHERE character_id = $3
                RETURNING life_energy
            """, energy_delta, datetime.now(), character_id)
            
            if not result:
                return None
            
            new_energy = result['life_energy']
            
            # Log energy change event
            await conn.execute("""
                INSERT INTO learning_events (
                    character_id, event_type, event_category,
                    context_data, success_score, importance_score
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, 
            character_id, 'energy_change', 'survival',
            json.dumps({
                'energy_delta': energy_delta,
                'event_type': event_type,
                'event_source': event_source,
                'new_energy': float(new_energy)
            }),
            0.7 if energy_delta > 0 else 0.3,
            0.5
            )
            
            self._query_count += 2
            return float(new_energy)
    
    async def get_character_survival_status(self, character_id: str) -> Dict:
        """Get character survival status with comprehensive calculation"""
        
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        try:
            async with self.get_connection() as conn:
                char_data = await conn.fetchrow("""
                    SELECT 
                        life_energy, 
                        survival_threshold, 
                        energy_decay_rate,
                        last_energy_update
                    FROM character_evolution 
                    WHERE character_id = $1
                """, character_id)
                
                self._query_count += 1
                
                if not char_data:
                    return {"status": "not_found", "character_id": character_id}
                
                # Calculate energy decay
                now = datetime.now()
                last_update = char_data['last_energy_update']
                
                # Handle timezone-naive datetime from database
                if last_update.tzinfo is None:
                    last_update = last_update.replace(tzinfo=timezone.utc)
                
                time_diff = now - last_update
                hours_passed = time_diff.total_seconds() / 3600
                
                current_energy = float(char_data['life_energy'])
                decay_rate = float(char_data['energy_decay_rate'])
                survival_threshold = float(char_data['survival_threshold'])
                
                # Calculate projected energy
                decay_amount = decay_rate * (hours_passed / 24)  # Daily decay rate
                projected_energy = max(0.0, current_energy - decay_amount)
                
                is_alive = projected_energy > survival_threshold
                
                # Determine status
                if projected_energy <= 0:
                    status = "dead"
                elif projected_energy <= survival_threshold:
                    status = "critical"
                elif projected_energy <= survival_threshold * 2:
                    status = "warning"
                else:
                    status = "healthy"
                
                return {
                    "character_id": character_id,
                    "current_energy": current_energy,
                    "projected_energy": projected_energy,
                    "survival_threshold": survival_threshold,
                    "is_alive": is_alive,
                    "hours_since_update": round(hours_passed, 2),
                    "status": status,
                    "decay_rate_daily": decay_rate,
                    "time_to_critical": self._calculate_time_to_critical(
                        projected_energy, decay_rate, survival_threshold
                    )
                }
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error getting survival status: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to get survival status: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error getting survival status: {e}")
            self._error_count += 1
            raise
    
    def _calculate_time_to_critical(self, current_energy: float, daily_decay: float, threshold: float) -> Optional[float]:
        """Calculate hours until critical energy level"""
        if current_energy <= threshold or daily_decay <= 0:
            return None
        
        energy_buffer = current_energy - threshold
        days_to_critical = energy_buffer / daily_decay
        return round(days_to_critical * 24, 1)  # Convert to hours
    
    # ==========================================
    # SESSION OPERATIONS - ROBUST
    # ==========================================
    
    async def create_session(self, 
                           session_id: str, 
                           topic: str, 
                           participants: List[str], 
                           max_rounds: int = 20) -> bool:
        """Create new autonomous session with validation"""
        
        # Validation
        if not session_id or not isinstance(session_id, str) or len(session_id) > 100:
            raise ValidationError(f"Invalid session_id: {session_id}")
        
        if not topic or not isinstance(topic, str) or len(topic) > 1000:
            raise ValidationError(f"Invalid topic: {topic}")
        
        if not participants or not isinstance(participants, list):
            raise ValidationError("Participants must be a non-empty list")
        
        for participant in participants:
            if not self._validate_character_id(participant):
                raise ValidationError(f"Invalid participant: {participant}")
        
        if not (1 <= max_rounds <= 100):
            raise ValidationError(f"Invalid max_rounds: {max_rounds}")
        
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO autonomous_sessions (
                        session_id, topic, participants_json, max_rounds
                    ) VALUES ($1, $2, $3, $4)
                """, session_id, topic, json.dumps(participants), max_rounds)
                
                self._query_count += 1
                logger.info(f"✅ Created session: {session_id}")
                return True
                
        except asyncpg.exceptions.UniqueViolationError:
            logger.warning(f"⚠️ Session {session_id} already exists")
            return False
            
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error creating session: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to create session: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error creating session: {e}")
            self._error_count += 1
            raise
    
    async def store_speech_metadata(self, 
                                  speech_id: str,
                                  session_id: str,
                                  character_id: str,
                                  emotion: str,
                                  duration_seconds: float,
                                  voice_config: Dict = None,
                                  **kwargs) -> bool:
        """Store speech metadata with validation"""
        
        # Validation
        try:
            uuid.UUID(speech_id)  # Validate UUID format
        except ValueError:
            raise ValidationError(f"Invalid speech_id format: {speech_id}")
        
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        if not session_id:
            raise ValidationError("session_id is required")
        
        if not emotion or len(emotion) > 50:
            raise ValidationError(f"Invalid emotion: {emotion}")
        
        try:
            duration_seconds = float(duration_seconds)
            if not (0.0 <= duration_seconds <= 300.0):  # Max 5 minutes
                raise ValidationError(f"Invalid duration: {duration_seconds}")
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid duration: {duration_seconds}")
        
        try:
            async with self.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO session_speeches (
                        id, session_id, character_id, emotion, duration_seconds,
                        voice_config, round_number, triggered_by, 
                        generation_time_ms, tts_provider, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                speech_id, session_id, character_id, emotion, duration_seconds,
                json.dumps(voice_config) if voice_config else None,
                kwargs.get('round_number'),
                kwargs.get('triggered_by'),
                kwargs.get('generation_time_ms'),
                kwargs.get('tts_provider'),
                datetime.now()
                )
                
                self._query_count += 1
                return True
                
        except asyncpg.exceptions.ForeignKeyViolationError:
            logger.warning(f"⚠️ Foreign key violation storing speech {speech_id}")
            return False
            
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error storing speech metadata: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to store speech metadata: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error storing speech metadata: {e}")
            self._error_count += 1
            raise
    
    # ==========================================
    # LEARNING EVENTS - ROBUST
    # ==========================================
    
    async def record_learning_event(self, 
                                   character_id: str,
                                   session_id: str,
                                   event_type: str,
                                   context_data: Dict,
                                   qdrant_memory_id: str = None,
                                   success_score: float = None,
                                   importance_score: float = 0.5) -> str:
        """Record learning event with validation"""
        
        # Validation
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        if not event_type or len(event_type) > 50:
            raise ValidationError(f"Invalid event_type: {event_type}")
        
        if not isinstance(context_data, dict):
            raise ValidationError("context_data must be a dictionary")
        
        if success_score is not None:
            try:
                success_score = float(success_score)
                if not (0.0 <= success_score <= 1.0):
                    raise ValidationError(f"success_score out of range: {success_score}")
            except (TypeError, ValueError):
                raise ValidationError(f"Invalid success_score: {success_score}")
        
        try:
            importance_score = float(importance_score)
            if not (0.0 <= importance_score <= 1.0):
                raise ValidationError(f"importance_score out of range: {importance_score}")
        except (TypeError, ValueError):
            raise ValidationError(f"Invalid importance_score: {importance_score}")
        
        if qdrant_memory_id:
            try:
                uuid.UUID(qdrant_memory_id)
            except ValueError:
                raise ValidationError(f"Invalid qdrant_memory_id format: {qdrant_memory_id}")
        
        try:
            async with self.get_connection() as conn:
                event_id = await conn.fetchval("""
                    INSERT INTO learning_events (
                        character_id, session_id, event_type, context_data,
                        qdrant_memory_id, success_score, importance_score, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """, 
                character_id, session_id, event_type, json.dumps(context_data),
                qdrant_memory_id, success_score, importance_score, datetime.now()
                )
                
                self._query_count += 1
                event_id_str = str(event_id)
                logger.info(f"✅ Recorded learning event: {event_id_str}")
                return event_id_str
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error recording learning event: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to record learning event: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error recording learning event: {e}")
            self._error_count += 1
            raise
    
    async def get_character_learning_history(self, 
                                           character_id: str, 
                                           limit: int = 20,
                                           event_types: List[str] = None) -> List[Dict]:
        """Get character learning history with validation"""
        
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        if not (1 <= limit <= 100):
            raise ValidationError(f"Invalid limit: {limit}")
        
        try:
            async with self.get_connection() as conn:
                if event_types:
                    # Validate event types
                    if not isinstance(event_types, list) or not all(isinstance(et, str) for et in event_types):
                        raise ValidationError("event_types must be a list of strings")
                    
                    events = await conn.fetch("""
                        SELECT * FROM learning_events 
                        WHERE character_id = $1 AND event_type = ANY($2)
                        ORDER BY timestamp DESC 
                        LIMIT $3
                    """, character_id, event_types, limit)
                else:
                    events = await conn.fetch("""
                        SELECT * FROM learning_events 
                        WHERE character_id = $1
                        ORDER BY timestamp DESC 
                        LIMIT $2
                    """, character_id, limit)
                
                self._query_count += 1
                
                # Convert to dict and handle datetime serialization
                result = []
                for event in events:
                    event_dict = dict(event)
                    for key, value in event_dict.items():
                        if isinstance(value, datetime):
                            event_dict[key] = value.isoformat()
                        elif isinstance(value, uuid.UUID):
                            event_dict[key] = str(value)
                    result.append(event_dict)
                
                return result
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error getting learning history: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to get learning history: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error getting learning history: {e}")
            self._error_count += 1
            raise
    
    # ==========================================
    # ANALYTICS & HEALTH
    # ==========================================
    
    async def get_character_performance_dashboard(self, character_id: str) -> Dict:
        """Get character performance dashboard with error handling"""
        
        if not self._validate_character_id(character_id):
            raise ValidationError(f"Invalid character_id: {character_id}")
        
        try:
            async with self.get_connection() as conn:
                # Character overview
                char_data = await conn.fetchrow("""
                    SELECT * FROM character_evolution WHERE character_id = $1
                """, character_id)
                
                if not char_data:
                    return {"error": "Character not found", "character_id": character_id}
                
                # Recent activity (last 7 days)
                recent_activity = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as speeches_last_7_days,
                        AVG(duration_seconds) as avg_speech_duration
                    FROM session_speeches 
                    WHERE character_id = $1 
                    AND timestamp > $2
                """, character_id, datetime.now() - timedelta(days=7))
                
                # Learning performance (last 30 days)
                learning_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_learning_events,
                        AVG(success_score) as avg_success_score,
                        COUNT(*) FILTER (WHERE event_type = 'breakthrough') as breakthroughs
                    FROM learning_events 
                    WHERE character_id = $1 
                    AND timestamp > $2
                """, character_id, datetime.now() - timedelta(days=30))
                
                self._query_count += 3
                
                # Convert to serializable format
                character_data = dict(char_data)
                for key, value in character_data.items():
                    if isinstance(value, datetime):
                        character_data[key] = value.isoformat()
                
                return {
                    "character": character_data,
                    "recent_activity": dict(recent_activity) if recent_activity else {},
                    "learning_stats": dict(learning_stats) if learning_stats else {},
                    "generated_at": datetime.now().isoformat()
                }
                
        except asyncpg.exceptions.PostgresError as e:
            logger.error(f"❌ Database error getting dashboard: {e}")
            self._error_count += 1
            raise DatabaseError(f"Failed to get dashboard: {e}")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error getting dashboard: {e}")
            self._error_count += 1
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "status": "unknown",
            "state": self.state.value,
            "connected": self.state == ServiceState.READY,
            "pool_info": {},
            "response_time_ms": None,
            "query_count": self._query_count,
            "error_count": self._error_count,
            "error_rate": 0.0,
            "last_check": None,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # Basic connection test
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            # Pool information
            pool_info = {}
            if self.pool:
                try:
                    pool_info = {
                        "min_size": getattr(self.pool, '_minsize', 'unknown'),
                        "max_size": getattr(self.pool, '_maxsize', 'unknown'),
                        "current_size": len(getattr(self.pool, '_holders', [])),
                        "available": getattr(self.pool, '_queue', {}).qsize() if hasattr(getattr(self.pool, '_queue', None), 'qsize') else 'unknown'
                    }
                except:
                    pool_info = {"error": "Could not get pool info"}
            
            # Calculate error rate
            error_rate = self._error_count / max(self._query_count, 1)
            
            health_status.update({
                "status": "healthy" if error_rate < 0.1 else "degraded",
                "response_time_ms": response_time,
                "pool_info": pool_info,
                "error_rate": round(error_rate, 4),
                "last_check": datetime.now().isoformat()
            })
            
            self._last_health_check = time.time()
        
        except Exception as e:
            health_status.update({
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            })
        
        return health_status
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    def _validate_character_id(self, character_id: str) -> bool:
        """Validate character ID format"""
        if not isinstance(character_id, str):
            return False
        if not (1 <= len(character_id) <= 50):
            return False
        # Allow alphanumeric and underscore/dash
        return character_id.replace('_', '').replace('-', '').isalnum()
    
    def _parse_update_result(self, result: str) -> int:
        """Parse PostgreSQL UPDATE result"""
        try:
            if result.startswith('UPDATE '):
                return int(result.split()[-1])
            return 0
        except (ValueError, IndexError):
            return 0
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "state": self.state.value,
            "query_count": self._query_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._query_count, 1),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time()),
            "last_health_check": self._last_health_check
        }

# Global database service instance
db_service = DatabaseService()

# Set start time
db_service._start_time = time.time()