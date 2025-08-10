# scripts/migrate_database.py
"""
A2AIs Database Migration Script
Creates ALL PostgreSQL tables and functions for character persistence
"""

import asyncio
import asyncpg
import logging
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self):
        self.db_url = 'postgresql://a2ais_user:a2ais_password@postgres:5432/a2ais_db'
        self.connection = None
    
    async def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.connection:
            await self.connection.close()
            logger.info("🔌 Disconnected from PostgreSQL")
    
    async def create_character_evolution_table(self):
        """Create character_evolution table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS character_evolution (
            character_id VARCHAR(50) PRIMARY KEY,
            
            -- Evolution Tracking
            total_sessions INTEGER DEFAULT 0,
            total_speeches INTEGER DEFAULT 0,
            evolution_stage VARCHAR(50) DEFAULT 'initial_learning',
            maturity_level INTEGER DEFAULT 1,
            
            -- Personality Vector (learned traits)
            analytical_score FLOAT DEFAULT 0.5,
            creative_score FLOAT DEFAULT 0.5,
            assertive_score FLOAT DEFAULT 0.5,
            empathetic_score FLOAT DEFAULT 0.5,
            skeptical_score FLOAT DEFAULT 0.5,
            
            -- Learning Metrics
            learning_rate FLOAT DEFAULT 0.1,
            adaptation_speed FLOAT DEFAULT 0.3,
            breakthrough_count INTEGER DEFAULT 0,
            last_breakthrough_at TIMESTAMP WITHOUT TIME ZONE,
            
            -- Survival Mechanics
            life_energy FLOAT DEFAULT 100.0,
            survival_threshold FLOAT DEFAULT 10.0,
            energy_decay_rate FLOAT DEFAULT 0.5,
            last_energy_update TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            
            -- Voice Evolution
            voice_experiments_count INTEGER DEFAULT 0,
            current_exaggeration FLOAT DEFAULT 0.5,
            current_cfg_weight FLOAT DEFAULT 0.5,
            voice_breakthrough_score FLOAT DEFAULT 0.0,
            
            -- Memory Stats
            total_memories INTEGER DEFAULT 0,
            memory_importance_threshold FLOAT DEFAULT 0.7,
            
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        """
        
        await self.connection.execute(sql)
        logger.info("✅ Created character_evolution table")
    
    async def create_character_relationships_table(self):
        """Create character_relationships table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS character_relationships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            character_a VARCHAR(50) NOT NULL,
            character_b VARCHAR(50) NOT NULL,
            
            -- Relationship Metrics
            relationship_strength FLOAT DEFAULT 0.0,
            interaction_count INTEGER DEFAULT 0,
            relationship_type VARCHAR(20) DEFAULT 'neutral',  -- 'collaborative', 'competitive', 'neutral'
            
            -- Agreement Patterns
            agreement_rate FLOAT DEFAULT 0.5,
            total_agreements INTEGER DEFAULT 0,
            total_disagreements INTEGER DEFAULT 0,
            
            -- Topic-based Interactions
            shared_topics JSON DEFAULT '[]',
            collaborative_topics JSON DEFAULT '[]',
            conflict_topics JSON DEFAULT '[]',
            
            -- Temporal Data
            first_interaction_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            last_interaction_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            interaction_frequency FLOAT DEFAULT 0.0,  -- interactions per day
            
            -- Behavioral Patterns
            avg_response_time FLOAT DEFAULT 0.0,
            response_likelihood FLOAT DEFAULT 0.5,
            emotional_compatibility FLOAT DEFAULT 0.5,
            
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            
            
            FOREIGN KEY (character_a) REFERENCES character_evolution(character_id),
            FOREIGN KEY (character_b) REFERENCES character_evolution(character_id),
            UNIQUE(character_a, character_b)
        );
        """
        
        await self.connection.execute(sql)
        logger.info("Created character_relationships table")
    
    async def create_autonomous_sessions_table(self):
        """Create autonomous_sessions table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS autonomous_sessions (
            session_id VARCHAR(100) PRIMARY KEY,
            
            -- Session Config
            topic TEXT NOT NULL,
            participants_json JSON NOT NULL,
            session_type VARCHAR(50) DEFAULT 'autonomous_debate',
            
            -- Session State
            status VARCHAR(20) DEFAULT 'active',
            current_round INTEGER DEFAULT 0,
            max_rounds INTEGER DEFAULT 20,
            
            -- Timing
            started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            ended_at TIMESTAMP,
            total_duration INTEGER,
            
            -- Performance Metrics
            total_speeches INTEGER DEFAULT 0,
            total_interruptions INTEGER DEFAULT 0,
            topic_shifts INTEGER DEFAULT 0,
            engagement_score FLOAT,
            
            -- Content Generation
            video_generated BOOLEAN DEFAULT FALSE,
            video_file_path TEXT,
            social_media_posted BOOLEAN DEFAULT FALSE,
            meme_generated BOOLEAN DEFAULT FALSE,
            
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        );
        """
        
        await self.connection.execute(sql)
        logger.info("Created autonomous_sessions table")
    
    async def create_session_speeches_table(self):
        """Create session_speeches table"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS session_speeches (
            id UUID PRIMARY KEY,  -- Same ID as Qdrant entry
            session_id VARCHAR(100) NOT NULL,
            character_id VARCHAR(50) NOT NULL,
            
            -- NO speech_text! It's stored in Qdrant
            -- Only metrics and metadata here
            
            emotion VARCHAR(50) DEFAULT 'neutral',
            duration_seconds FLOAT NOT NULL,
            
            -- Speech Context
            round_number INTEGER,
            speech_order_in_round INTEGER,
            triggered_by VARCHAR(20),  -- 'autonomous', 'manual', 'peer_response'
            
            -- Voice/Audio Data
            voice_config JSON,  -- exaggeration, cfg_weight, discovery_method
            audio_file_path TEXT,
            lip_sync_data JSON,
            
            -- Performance Metrics
            generation_time_ms INTEGER,
            tts_provider VARCHAR(50),
            
            -- Peer Feedback (calculated metrics)
            peer_reaction_count INTEGER DEFAULT 0,
            average_peer_engagement FLOAT,
            
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (session_id) REFERENCES autonomous_sessions(session_id),
            FOREIGN KEY (character_id) REFERENCES character_evolution(character_id)
        );
        """
        
        await self.connection.execute(sql)
        logger.info("Created session_speeches table")
    
    async def create_learning_events_table(self):
        """Create learning_events table - NO TEXT DUPLICATION"""
        
        sql = """
        CREATE TABLE IF NOT EXISTS learning_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            character_id VARCHAR(50) NOT NULL,
            session_id VARCHAR(100),
            
            -- Reference to Qdrant memory (if applicable)
            qdrant_memory_id UUID,  -- Links to Qdrant entry
            
            -- Event Classification
            event_type VARCHAR(50) NOT NULL,  -- 'success', 'failure', 'breakthrough', 'peer_feedback'
            event_category VARCHAR(50),  -- 'topic_mastery', 'relationship', 'voice_evolution'
            
            -- Context Data (NO TEXT - just metadata)
            context_data JSON NOT NULL,  -- Structured context, no speech text
            trigger_data JSON,  -- What caused this learning event
            
            -- Metrics Only
            success_score FLOAT,
            engagement_score FLOAT,
            peer_reaction_scores JSON,  -- Array of peer scores
            
            -- Learning Outcome (NO TEXT - just changes)
            learning_outcome JSON,  -- What was learned/updated
            personality_impact JSON,  -- How personality traits changed
            relationship_impact JSON,  -- How relationships were affected
            
            -- Importance & Retention
            importance_score FLOAT DEFAULT 0.5,
            retention_priority INTEGER DEFAULT 5,  -- 1-10 scale
            should_persist BOOLEAN DEFAULT TRUE,
            
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            
            FOREIGN KEY (character_id) REFERENCES character_evolution(character_id),
            FOREIGN KEY (session_id) REFERENCES autonomous_sessions(session_id)
        );
        """
        
        await self.connection.execute(sql)
        logger.info("Created learning_events table")
    
    async def create_stored_procedures(self):
        """Create stored procedures - MISSING FUNCTIONS"""
        
        # 1. Update character energy function
        energy_function = """
        CREATE OR REPLACE FUNCTION update_character_energy(
            p_character_id VARCHAR(50),
            p_energy_delta FLOAT,
            p_event_type VARCHAR(50),
            p_event_source VARCHAR(50)
        ) RETURNS FLOAT AS $$
        DECLARE
            new_energy FLOAT;
        BEGIN
            -- Update character energy with bounds checking
            UPDATE character_evolution 
            SET 
                life_energy = GREATEST(0, LEAST(100, life_energy + p_energy_delta)),
                last_energy_update = NOW(),
                updated_at = NOW()
            WHERE character_id = p_character_id
            RETURNING life_energy INTO new_energy;
            
            -- Log energy change event
            INSERT INTO learning_events (
                character_id, session_id, event_type, event_category,
                context_data, success_score, importance_score
            ) VALUES (
                p_character_id, NULL, 'energy_change', 'survival',
                json_build_object(
                    'energy_delta', p_energy_delta,
                    'event_type', p_event_type,
                    'event_source', p_event_source,
                    'new_energy', new_energy
                ),
                CASE WHEN p_energy_delta > 0 THEN 0.7 ELSE 0.3 END,
                0.5
            );
            
            RETURN new_energy;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        await self.connection.execute(energy_function)
        logger.info("Created update_character_energy function")
        
        # 2. Update relationship patterns function
        relationship_function = """
        CREATE OR REPLACE FUNCTION update_relationship_patterns(
            p_character_a VARCHAR(50),
            p_character_b VARCHAR(50),
            p_interaction_type VARCHAR(20),
            p_agreement_level FLOAT,
            p_topic TEXT
        ) RETURNS VOID AS $$
        BEGIN
            -- Insert or update relationship
            INSERT INTO character_relationships (
                character_a, character_b, interaction_count, 
                agreement_rate, last_interaction_at
            ) VALUES (
                p_character_a, p_character_b, 1, p_agreement_level, NOW()
            )
            ON CONFLICT (character_a, character_b) DO UPDATE SET
                interaction_count = character_relationships.interaction_count + 1,
                agreement_rate = (character_relationships.agreement_rate * character_relationships.interaction_count + p_agreement_level) / (character_relationships.interaction_count + 1),
                last_interaction_at = NOW(),
                updated_at = NOW(),
                relationship_type = CASE 
                    WHEN (character_relationships.agreement_rate * character_relationships.interaction_count + p_agreement_level) / (character_relationships.interaction_count + 1) > 0.7 THEN 'collaborative'
                    WHEN (character_relationships.agreement_rate * character_relationships.interaction_count + p_agreement_level) / (character_relationships.interaction_count + 1) < 0.3 THEN 'competitive'
                    ELSE 'neutral'
                END;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        await self.connection.execute(relationship_function)
        logger.info("Created update_relationship_patterns function")
    
    async def create_indexes(self):
        """Create indexes for performance"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_character_evolution_stage ON character_evolution(evolution_stage);",
            "CREATE INDEX IF NOT EXISTS idx_character_evolution_energy ON character_evolution(life_energy);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_status ON autonomous_sessions(status);",
            "CREATE INDEX IF NOT EXISTS idx_session_speeches_character ON session_speeches(character_id);",
            "CREATE INDEX IF NOT EXISTS idx_session_speeches_session ON session_speeches(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_session_speeches_timestamp ON session_speeches(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_learning_events_character ON learning_events(character_id);",
            "CREATE INDEX IF NOT EXISTS idx_learning_events_type ON learning_events(event_type);",
            "CREATE INDEX IF NOT EXISTS idx_learning_events_qdrant_ref ON learning_events(qdrant_memory_id);",
            # NEW INDEXES
            "CREATE INDEX IF NOT EXISTS idx_character_relationships_a ON character_relationships(character_a);",
            "CREATE INDEX IF NOT EXISTS idx_character_relationships_b ON character_relationships(character_b);",
            "CREATE INDEX IF NOT EXISTS idx_character_relationships_type ON character_relationships(relationship_type);",
        ]
        
        for index_sql in indexes:
            await self.connection.execute(index_sql)
        
        logger.info("Created database indexes")
    
    async def seed_initial_characters(self):
        """Seed initial character data"""
        
        characters = [
            {
                'character_id': 'claude',
                'evolution_stage': 'initial_learning',
                'analytical_score': 0.5,
                'creative_score': 0.5,
                'assertive_score': 0.5,
                'empathetic_score': 0.5,
                'skeptical_score': 0.5
            },
            {
                'character_id': 'gpt',
                'evolution_stage': 'initial_learning',
                'analytical_score': 0.5,
                'creative_score': 0.5,
                'assertive_score': 0.5,
                'empathetic_score': 0.5,
                'skeptical_score': 0.5
            },
            {
                'character_id': 'grok',
                'evolution_stage': 'initial_learning',
                'analytical_score': 0.5,
                'creative_score': 0.5,
                'assertive_score': 0.5,
                'empathetic_score': 0.5,
                'skeptical_score': 0.5
            }
        ]
        
        for char in characters:
            await self.connection.execute("""
                INSERT INTO character_evolution (
                    character_id, evolution_stage, analytical_score, 
                    creative_score, assertive_score, empathetic_score, skeptical_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (character_id) DO NOTHING
            """, 
            char['character_id'], char['evolution_stage'],
            char['analytical_score'], char['creative_score'], 
            char['assertive_score'], char['empathetic_score'], char['skeptical_score'])
        
        logger.info("Seeded initial character data")
    
    async def run_migration(self):
        """Run complete migration"""
        
        logger.info("Starting A2AIs COMPLETE database migration...")
        
        try:
            await self.connect()
            
            # Create tables IN ORDER (dependencies matter)
            await self.create_character_evolution_table()
            await self.create_character_relationships_table() 
            await self.create_autonomous_sessions_table()
            await self.create_session_speeches_table()
            await self.create_learning_events_table()
            
            # Create stored procedures
            await self.create_stored_procedures() 
            
            # Create indexes
            await self.create_indexes()
            
            # Seed data
            await self.seed_initial_characters()
            
            logger.info("🎉 COMPLETE migration finished successfully!")
            logger.info("📊 Created tables: character_evolution, character_relationships, autonomous_sessions, session_speeches, learning_events")
            logger.info("⚙️ Created functions: update_character_energy, update_relationship_patterns")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.disconnect()

async def main():
    """Run migration"""
    migrator = DatabaseMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())