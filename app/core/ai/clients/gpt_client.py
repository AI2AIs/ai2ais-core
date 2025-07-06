# app/core/ai/clients/gpt_client.py
import logging
import asyncio
from typing import Dict, Optional
from openai import AsyncOpenAI
from app.config.settings import settings

logger = logging.getLogger(__name__)

class GPTAPIClient:
    """Real OpenAI GPT API client"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the OpenAI client"""
        if self._initialized:
            return True
            
        if not self.api_key:
            logger.error("❌ OpenAI API key not configured")
            return False
            
        try:
            self.client = AsyncOpenAI(api_key=self.api_key)
            
            # Test connection
            test_response = await self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
            self._initialized = True
            logger.info("✅ GPT API client initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPT API: {e}")
            return False
    
    async def generate_response(self, prompt: str) -> str:
        """Generate GPT response"""
        
        if not await self.initialize():
            raise Exception("GPT API not available")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                max_tokens=150,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_text = response.choices[0].message.content.strip()
            logger.info(f"✅ GPT API response: {raw_text[:50]}...")
            
            return raw_text
            
        except Exception as e:
            logger.error(f"❌ GPT API call failed: {e}")
            raise

# Global instance
gpt_api_client = GPTAPIClient()