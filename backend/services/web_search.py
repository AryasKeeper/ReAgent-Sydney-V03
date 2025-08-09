"""Web search service using Tavily API"""
import httpx
import logging
from typing import Optional, Dict
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    """Handles web searches for weather, time, and general information"""
    
    def __init__(self):
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com"
    
    async def search_weather_time(self, query: str) -> str:
        """Search for weather or time information"""
        
        # Default to Sydney if location not specified
        if "sydney" not in query.lower():
            if "weather" in query.lower():
                query = "current weather in Sydney Australia"
            elif "time" in query.lower():
                query = "current time in Sydney Australia"
        
        if settings.USE_MOCK:
            return self._get_mock_weather_time(query)
        
        try:
            result = await self._tavily_search(query)
            if result and result.get("answer"):
                return result["answer"]
            else:
                return self._get_fallback_response(query)
                
        except Exception as e:
            logger.error(f"Weather/time search error: {e}")
            return self._get_fallback_response(query)
    
    async def _tavily_search(self, query: str) -> Optional[Dict]:
        """Execute Tavily API search"""
        if not self.tavily_api_key:
            logger.warning("Tavily API key not configured")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": True,
                        "max_results": 3
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Tavily API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return None
    
    def _get_mock_weather_time(self, query: str) -> str:
        """Return mock weather/time data for testing"""
        if "weather" in query.lower():
            return "The weather in Sydney is currently 22°C (72°F) with partly cloudy skies. Winds are light from the northeast at 10 km/h."
        elif "time" in query.lower():
            # Calculate Sydney time (AEDT = UTC+11)
            from datetime import timezone, timedelta
            sydney_tz = timezone(timedelta(hours=11))  # AEDT
            sydney_time = datetime.now(sydney_tz)
            return f"The current time in Sydney is {sydney_time.strftime('%I:%M %p on %A, %B %d, %Y')} (AEDT)."
        else:
            return "Sydney is experiencing typical autumn weather with mild temperatures."
    
    def _get_fallback_response(self, query: str) -> str:
        """Fallback response when search fails"""
        if "weather" in query.lower():
            return "I'm unable to fetch current weather data. Sydney typically has a temperate climate with warm summers and mild winters."
        elif "time" in query.lower():
            return "I'm unable to fetch the exact time. Sydney is in the AEDT timezone (UTC+11 during daylight saving)."
        else:
            return "I'm having trouble accessing that information right now."

# Global web search instance
web_search = WebSearchService()