"""Simplified AI router using env-configured OpenAI model(s)"""
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
            model_primary = settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else "gpt-4o-mini"
            model_fallback = (
                settings.OPENAI_MODEL_FALLBACK if hasattr(settings, "OPENAI_MODEL_FALLBACK") and settings.OPENAI_MODEL_FALLBACK else model_primary
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Agent Whisperer, a Sydney real estate assistant. "
                        "You have tools: Brave Search (discovery), Firecrawl (scrape), and optional JS rendering via Browserless. "
                        "For live info: plan → search → open → extract → synthesize. "
                        "Be concise, accurate, and cite sources when web info is used."
                    ),
                }
            ]
            
            if history:
                for msg in history[-5:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": message})
            
            stream = await self.client.chat.completions.create(
                model=model_primary,
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Primary model error: {e}")
            # Try fallback model
            try:
                stream = await self.client.chat.completions.create(
                    model=model_fallback,
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