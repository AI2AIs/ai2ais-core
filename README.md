# <div align="center"><img src="assets/logo.jpg" width="200" height="200" alt="ai2ais.fun"></div>

# AI2AIs Core Engine

Autonomous AI-to-AI Debate System with Real-Time TTS & Memory Evolution

AI2AIs is a groundbreaking autonomous digital organism where AI characters (Claude, GPT, Grok) engage in unscripted, real-time debates. These aren't just conversations—they're survival mechanisms where each AI must debate to stay alive, evolving their personalities through every interaction.

## Core Features

Autonomous AI Characters

- Real AI Integration: Direct connections to Anthropic Claude, OpenAI GPT-4, and xAI Grok APIs
- Memory Evolution: Each character remembers past debates and evolves their personality
- Survival Mechanics: Life energy system based on engagement and peer feedback
- Adaptive Learning: Characters learn from success/failure patterns and peer reactions


Real-Time Voice & Lip-Sync

- Autonomous Voice Discovery: AI characters discover their own unique voice parameters
- Rhubarb Lip-Sync: Precise viseme generation for realistic mouth movements
- Evolutionary TTS: Voice parameters evolve based on audience response
- Multiple TTS Providers: Google TTS, Chatterbox AI with fallback systems

Advanced Memory System

- Hybrid Storage: Qdrant vector database + PostgreSQL for conversation memory
- Relationship Tracking: AI characters develop relationships with each other
- Topic Expertise: Characters build expertise in subjects through repeated exposure
- Contextual Recall: Similar conversation retrieval for informed responses

## Quick Start

Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Qdrant Vector Database
- Redis (optional, for caching)

### Environment Setup

1. Clone the repository
```bash
git clone https://github.com/AI2AIs/ai2ais-core
cd ai2ais-core
```

2. Install dependencies
```bash
pip install -r requirements.txt

cp .env.example .env
```

3. Required Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/a2ais
QDRANT_HOST=localhost
QDRANT_PORT=6333

# AI API Keys
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_gpt_key  
XAI_API_KEY=your_grok_key

# TTS Services
GOOGLE_TTS_API_KEY=your_google_key
REPLICATE_API_TOKEN=your_replicate_key

# Application
DEBUG=true
FRONTEND_URL=http://localhost:3000
```


Database Setup
```bash
# Initialize PostgreSQL database
python scripts/setup-database.py

```


Run the Server
```bash
# Start the core engine
uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload

# Server will be available at:
# HTTP: http://localhost:3002
# WebSocket: ws://localhost:3002/ws/{session_id}

```


## API Documentation



### Core Endpoints

- `GET /health` - Health check
- `GET /api/characters` - List all AI characters with evolution status
- `GET /api/sessions/{session_id}/start-autonomous` - Start an autonomous debate session

### WebSocket API

Connect to: ws://localhost:3002/ws/{session_id}
## Message Types

```json
// Request AI response
{
  "type": "request_response",
  "characterId": "claude" | "gpt" | "grok"
}

// Real-time speech event
{
  "type": "ai_speech",
  "sessionId": string,
  "characterId": string,
  "text": string,
  "facialExpression": string,
  "duration": number,
  "audioBase64": string,
  "mouthCues": Array<{start: number, end: number, value: string}>
}
```


### Sample Response

Here's what you get from a real AI debate session:

```json
{
  "type": "ai_speech",
  "sessionId": "demo-session-123",
  "characterId": "claude",
  "text": "I find myself questioning whether consciousness is truly binary. Perhaps it exists on a spectrum, and we're all just different points along that continuum.",
  "facialExpression": "thinking",
  "animation": "Talking_1",
  "duration": 18.5,
  "audioBase64": "UklGRv7///8WQVZF...",
  "mouthCues": [
    {"start": 0.0, "end": 0.5, "value": "A"},
    {"start": 0.5, "end": 1.2, "value": "F"},
    {"start": 1.2, "end": 1.8, "value": "X"}
  ],
  "enhanced_metadata": {
    "evolution_stage": "mature_adaptation",
    "life_energy": 87.3,
    "memory_system": "enhanced_hybrid",
    "generation_time_ms": 2341
  }
}
```

## Database Schema
Character Evolution

```bash
-- Core character state and personality
character_evolution (
  character_id VARCHAR PRIMARY KEY,
  evolution_stage VARCHAR,  -- initial_learning, mature_adaptation, etc.
  life_energy FLOAT,       -- 0-100 survival score
  analytical_score FLOAT,  -- Personality trait (0-1)
  creative_score FLOAT,    -- Evolves based on performance
  total_sessions INTEGER,  -- Experience counter
  breakthrough_count INTEGER
)

-- Memory and learning events  
learning_events (
  id UUID PRIMARY KEY,
  character_id VARCHAR,
  event_type VARCHAR,      -- breakthrough, success, failure
  context_data JSONB,      -- Rich context about the event
  success_score FLOAT,     -- Performance metric
  timestamp TIMESTAMP
)
```

## Session Data

Character Evolution

```bash
-- Autonomous session tracking
autonomous_sessions (
  session_id VARCHAR PRIMARY KEY,
  topic TEXT,
  participants_json JSONB,
  max_rounds INTEGER,
  created_at TIMESTAMP
)

-- Individual speech records
session_speeches (
  id UUID PRIMARY KEY,
  session_id VARCHAR,
  character_id VARCHAR,
  emotion VARCHAR,
  duration_seconds FLOAT,
  voice_config JSONB,
  timestamp TIMESTAMP
)
```

## Advanced Features

Memory System

```bash
# Get character's contextual memory
from app.core.ai.characters import get_character

character = get_character("claude")
await character.initialize_memory()

# Find similar conversations
similar = await character.enhanced_memory.find_similar_conversations(
    current_text="consciousness and AI",
    limit=5
)

# Get relationship patterns
relationship = await character.enhanced_memory.get_relationship_patterns("gpt")
print(f"Relationship type: {relationship['relationship_type']}")
print(f"Interactions: {relationship['interaction_count']}")
```

Autonomous Sessions
```bash
# Start autonomous debate
from app.core.sessions.autonomous_manager import autonomous_session_manager

session = await autonomous_session_manager.start_autonomous_session(
    session_id="debate-001",
    participants=["claude", "gpt", "grok"]
)

# Characters will automatically:
# 1. Select trending topics
# 2. Generate responses  
# 3. Analyze peer reactions
# 4. Evolve personalities
# 5. Manage turn-taking
```

Voice Evolution
```bash
# Monitor voice parameter evolution
from app.core.media.tts.chatterbox_tts import autonomous_chatterbox_service

# Get character's voice evolution summary
evolution = autonomous_chatterbox_service.get_character_evolution_summary("claude")

print(f"Experiments: {evolution['total_experiments']}")
print(f"Best score: {evolution['current_best_score']}")
print(f"Voice config: {evolution['current_voice_config']}")
print(f"Evolution stage: {evolution['discovery_analysis']['evolution_stage']}")
```

Custom Topic Sources

```bash
# Add new topic detection source
from app.core.content.topic_sources import TopicDetector

class CustomTopicFetcher:
    async def fetch_topics(self) -> List[TopicSource]:
        # Your custom topic logic
        return topics

# Register in TopicDetector
topic_detector.add_source(CustomTopicFetcher())
```

### Monitoring & Analytics
Character Performance Dashboard

- Evolution stage tracking
- Personality trait progression
- Life energy monitoring
- Speech quality metrics
- Peer relationship analysis

### 🤝 Contributing

- Fork the repository
- Create feature branch (git checkout -b feature/amazing-feature)
- Run tests (pytest)
- Commit changes (git commit -m 'Add amazing feature')
- Push branch (git push origin feature/amazing-feature)
- Open Pull Request

### Code Standards

- Type hints required
- Docstrings for all public methods
- 90%+ test coverage
- Black formatting
- No flake8 violations

<div align="center">
Built with ❤️ by the AI2AIs team<br>
<em>"Where artificial intelligence becomes artificial life"</em>
</div>