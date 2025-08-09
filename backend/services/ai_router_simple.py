"""Simplified AI router using only GPT-5"""
import logging
from typing import AsyncGenerator, List, Dict, Optional
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class SimpleAIRouter:
    """Simple router using only GPT-5"""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("GPT-5 client initialized")
        else:
            logger.warning("No OpenAI API key found")
    
    async def process_message(
        self, 
        message: str, 
        session_id: str,
        history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Process a message using GPT-5"""
        
        if not self.client:
            yield "API key not configured. Please add your OpenAI API key to the .env file."
            return
        
        try:
            messages = [
                {"role": "system", "content": "You are Agent Whisperer, powered by GPT-5 - OpenAI's most advanced AI model. You specialize in Sydney real estate and can help with property searches, market analysis, investment strategies, and general questions. Be helpful, accurate, and conversational."}
            ]
            
            if history:
                for msg in history[-5:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": message})
            
            # Use GPT-5
            stream = await self.client.chat.completions.create(
                model="gpt-5",  # GPT-5 - announced August 7, 2025
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"GPT-5 error: {e}")
            # Try fallback to GPT-4 if GPT-5 fails
            try:
                stream = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                yield f"Error connecting to OpenAI: {str(e)[:100]}"

# Global instance
simple_ai_router = SimpleAIRouter()