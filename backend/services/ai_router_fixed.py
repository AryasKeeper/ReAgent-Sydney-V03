"""Fixed AI router with proper error handling and GPT-5/GPT-4 fallback"""
import logging
import os
from typing import AsyncGenerator, List, Dict, Optional
from openai import AsyncOpenAI
import asyncio

logger = logging.getLogger(__name__)

class FixedAIRouter:
    """AI Router with comprehensive error handling and model fallback"""
    
    def __init__(self):
        """Initialize with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        else:
            self.client = None
            logger.error("No OpenAI API key found in environment")
    
    async def process_message(
        self, 
        message: str, 
        session_id: str,
        history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Process message with automatic model fallback"""
        
        # Check if client is initialized
        if not self.client:
            yield "I need an OpenAI API key to function. Please add OPENAI_API_KEY to your .env file."
            return
        
        # Build messages array
        messages = [
            {
                "role": "system", 
                "content": """You are Agent Whisperer, an advanced AI assistant specializing in Sydney real estate, powered by GPT-5.

Your capabilities include:
1. **Property Search & Analysis**: Find properties, analyze listings, compare neighborhoods
2. **Market Intelligence**: Trends, pricing insights, investment opportunities
3. **Buyer Assistance**: Property matching, area recommendations, budget planning
4. **Seller Support**: Valuation estimates, market timing, listing optimization
5. **General Knowledge**: Weather, news, calculations, and any other questions
6. **Deep Analysis**: Complex market analysis, investment strategies, detailed comparisons

Be helpful, accurate, and conversational. Provide comprehensive answers when asked about your capabilities."""
            }
        ]
        
        # Add conversation history if provided
        if history:
            # Only include last 5 messages to avoid token limits
            for msg in history[-5:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Try GPT-5 first, then GPT-4 Turbo, then GPT-3.5
        models_to_try = [
            ("gpt-5", 2000),           # GPT-5 with 2000 max tokens
            ("gpt-4-turbo-preview", 1500),  # GPT-4 Turbo fallback
            ("gpt-4", 1000),           # Standard GPT-4
            ("gpt-3.5-turbo", 800)     # Final fallback
        ]
        
        last_error = None
        
        for model_name, max_tokens in models_to_try:
            try:
                logger.info(f"Attempting to use model: {model_name}")
                
                # Create the chat completion with streaming
                stream = await self.client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    timeout=30  # 30 second timeout
                )
                
                # Stream the response
                logger.info(f"Successfully connected to {model_name}")
                
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                
                # If successful, we're done
                return
                
            except asyncio.TimeoutError:
                last_error = f"Timeout with {model_name}"
                logger.warning(f"Timeout error with {model_name}, trying next model")
                continue
                
            except Exception as e:
                last_error = f"{model_name}: {str(e)}"
                logger.warning(f"Error with {model_name}: {e}")
                
                # Special handling for specific error messages
                error_str = str(e).lower()
                
                if "model does not exist" in error_str or "invalid model" in error_str:
                    logger.info(f"Model {model_name} not available, trying fallback")
                    continue
                    
                if "rate limit" in error_str:
                    logger.warning("Rate limit hit, waiting 2 seconds")
                    await asyncio.sleep(2)
                    continue
                    
                if "api key" in error_str:
                    yield "There's an issue with the API key. Please check your OpenAI API key in the .env file."
                    return
                    
                # For other errors, try next model
                continue
        
        # If all models failed, provide detailed error
        logger.error(f"All models failed. Last error: {last_error}")
        
        # Provide a helpful fallback response
        if "in-depth" in message.lower() or "capabilities" in message.lower():
            yield """I apologize for the connection issue. Let me tell you about my capabilities:

As Agent Whisperer, I can help you with:

**Sydney Real Estate Services:**
• Property searches and recommendations
• Market analysis and trends
• Investment opportunity assessment
• Neighborhood comparisons
• Price estimates and valuations

**General Assistance:**
• Weather updates for Sydney
• Current time information
• General questions and conversations
• Calculations and data analysis

**Technical Note:** I'm currently experiencing some API connectivity issues, but I'm still here to help with your Sydney real estate needs. Please try rephrasing your question or ask something specific about properties or the market."""
        else:
            yield f"I'm having trouble processing that request. Error: {last_error}. Please try again with a simpler question."

# Create global instance
fixed_ai_router = FixedAIRouter()