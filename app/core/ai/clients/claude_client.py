# app/core/ai/clients/claude_client.py
import logging
import asyncio
from typing import Dict, Optional
from anthropic import AsyncAnthropic
from app.config.settings import settings

logger = logging.getLogger(__name__)

class ClaudeAPIClient:
    """Real Anthropic Claude API client"""
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the Anthropic client"""
        if self._initialized:
            return True
            
        if not self.api_key:
            logger.error("❌ Anthropic API key not configured")
            return False
            
        try:
            self.client = AsyncAnthropic(api_key=self.api_key)
            
            # Test connection
            test_response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            self._initialized = True
            logger.info("✅ Claude API client initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Claude API: {e}")
            return False
    
    async def generate_response(self, prompt: str) -> str:
        """Generate Claude response"""
        
        if not await self.initialize():
            raise Exception("Claude API not available")
        
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=150,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_text = response.content[0].text.strip()
            logger.info(f"✅ Claude API response: {raw_text[:50]}...")
            
            return raw_text
            
        except Exception as e:
            logger.error(f"❌ Claude API call failed: {e}")
            raise

# Global instance
claude_api_client = ClaudeAPIClient()