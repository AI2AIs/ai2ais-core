# app/core/ai/clients/grok_client.py
import logging
import asyncio
from typing import Dict, Optional
from xai_sdk import Client
from xai_sdk.chat import user
from app.config.settings import settings

logger = logging.getLogger(__name__)

class GrokAPIClient:
    """Real xAI Grok API client using official SDK"""
    
    def __init__(self):
        self.api_key = settings.XAI_API_KEY
        self.client = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the xAI client"""
        if self._initialized:
            return True
            
        if not self.api_key:
            logger.error("xAI API key not configured")
            return False
            
        try:
            self.client = Client(api_key=self.api_key)
            
            # Test connection
            test_chat = self.client.chat.create(
                model="grok-3-mini",
                messages=[user("Hi")],
                temperature=0.7,
            )
            test_response = test_chat.sample()
            
            self._initialized = True
            logger.info("Grok API client initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Grok API: {e}")
            return False
    
    async def generate_response(self, prompt: str) -> str:
        """Generate Grok response"""
        
        if not await self.initialize():
            raise Exception("Grok API not available")
        
        try:
            # Create chat with user prompt
            chat = self.client.chat.create(
                model="grok-3-mini",
                messages=[user(prompt)],
                temperature=0.8,
            )
            
            # Sample response
            response = chat.sample()
            
            # Extract content
            raw_text = response.content.strip()
            logger.info(f"Grok API response: {raw_text[:50]}...")
            
            return raw_text
            
        except Exception as e:
            logger.error(f"Grok API call failed: {e}")
            raise

# Global instance
grok_api_client = GrokAPIClient()