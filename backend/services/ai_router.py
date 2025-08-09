"""AI model routing and integration service"""
import os
import logging
from typing import AsyncGenerator, List, Dict, Optional
import httpx
import json
try:
    from openai import AsyncOpenAI  # type: ignore
except Exception:
    AsyncOpenAI = None  # type: ignore

try:
    from anthropic import AsyncAnthropic  # type: ignore
except Exception:
    AsyncAnthropic = None  # type: ignore

from config import settings

logger = logging.getLogger(__name__)

class AIRouter:
    """Routes requests to appropriate AI models"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if AsyncOpenAI and settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        
        if AsyncAnthropic and settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialized")
    
    async def process_message(
        self, 
        message: str, 
        session_id: str,
        history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Process a message and stream the response"""
        
        # Check if we have API keys configured
        if not self.openai_client and not self.anthropic_client:
            # Fallback to mock responses if no API keys
            logger.warning("No AI API keys configured, using fallback responses")
            yield "I'm currently running in limited mode. "
            yield "To enable full AI capabilities, please configure OpenAI or Anthropic API keys. "
            yield "For now, I can help with basic Sydney real estate queries."
            return
        
        # Determine complexity and route accordingly
        use_claude = self._should_use_claude(message)
        
        try:
            if use_claude and self.anthropic_client:
                async for chunk in self._stream_claude_response(message, history):
                    yield chunk
            elif self.openai_client:
                async for chunk in self._stream_openai_response(message, history):
                    yield chunk
            else:
                yield "I'm currently unable to process your request. Please ensure API keys are configured."
                
        except Exception as e:
            logger.error(f"AI routing error: {e}")
            yield "I encountered an error processing your request. Please try again."
    
    def _should_use_claude(self, message: str) -> bool:
        """Determine if we should use Claude 4 based on query complexity"""
        # Claude 4 excels at deep reasoning, coding, and complex analysis
        # GPT-5 is better for general conversation and speed
        
        complex_keywords = [
            "analyze", "explain", "compare", "strategy",
            "investment", "portfolio", "market analysis",
            "code", "debug", "implement", "architecture",
            "reasoning", "think", "complex", "detailed"
        ]
        
        message_lower = message.lower()
        is_complex = any(keyword in message_lower for keyword in complex_keywords)
        is_long = len(message.split()) > 30  # Increased threshold for latest models
        needs_reasoning = "step by step" in message_lower or "think" in message_lower
        
        return is_complex or is_long or needs_reasoning
    
    async def _stream_openai_response(self, message: str, history: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream response from OpenAI"""
        messages = [
            {"role": "system", "content": "You are Agent Whisperer, powered by GPT-5 - an advanced AI real estate specialist for Sydney. You have access to real-time data, market analysis capabilities, and can provide detailed insights about properties, suburbs, market trends, and investment strategies. Be conversational, helpful, and provide accurate, up-to-date information."}
        ]
        
        if history:
            for msg in history[-5:]:  # Include last 5 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        try:
            stream = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",  # GPT-4 Turbo - OpenAI's most capable model
                messages=messages,
                stream=True,
                temperature=0.7
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"OpenAI streaming error: {e}")
            logger.error(f"Full traceback: {error_details}")
            print(f"DEBUG - OpenAI Error: {e}")
            yield f"I'm having trouble connecting to the AI service. Error: {str(e)[:100]}"
    
    async def _stream_claude_response(self, message: str, history: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream response from Claude"""
        system = "You are Agent Whisperer, powered by Claude 4 Sonnet - an advanced AI with extended reasoning capabilities. You specialize in Sydney real estate with deep analytical abilities for market trends, investment strategies, and complex property analysis. Use your step-by-step thinking to provide thorough, insightful responses."
        
        messages = []
        if history:
            for msg in history[-5:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        try:
            async with self.anthropic_client.messages.stream(
                model="claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet - Anthropic's latest model
                max_tokens=1024,
                system=system,
                messages=messages,
                temperature=0.7
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            yield "I'm having trouble connecting to the AI service."

# Global AI router instance
ai_router = AIRouter()
