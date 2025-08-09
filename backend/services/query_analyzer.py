"""Intelligent query analyzer and router for Agent Whisperer"""
import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Types of queries we can handle"""
    WEATHER = "weather"
    TIME = "time"
    NEWS = "news"
    PROPERTY_SEARCH = "property_search"
    PROPERTY_ANALYSIS = "property_analysis"
    GENERAL_CHAT = "general_chat"
    GREETING = "greeting"
    CALCULATION = "calculation"
    WEB_SEARCH = "web_search"
    
class QueryAnalyzer:
    """Analyzes user queries to determine intent and required tools"""
    
    def __init__(self):
        # Keywords for different query types
        self.weather_keywords = ["weather", "temperature", "rain", "sunny", "cloudy", "forecast", "hot", "cold"]
        self.time_keywords = ["time", "clock", "hour", "what time", "current time"]
        self.news_keywords = ["news", "happening", "latest", "current events", "today's news"]
        self.property_keywords = ["property", "house", "apartment", "bedroom", "real estate", 
                                 "buy", "sell", "rent", "sale", "price", "suburb", "home",
                                 "unit", "townhouse", "villa", "land", "auction"]
        self.greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", 
                                "good evening", "how are you", "what's up"]
        self.calculation_keywords = ["calculate", "compute", "solve", "math", "+", "-", "*", "/", "="]
        
    def analyze_query(self, query: str) -> Tuple[QueryType, Dict]:
        """
        Analyze a query and return its type and extracted parameters
        
        Returns:
            Tuple of (QueryType, parameters_dict)
        """
        query_lower = query.lower()
        
        # Check for greetings first
        if self._is_greeting(query_lower):
            return QueryType.GREETING, {}
            
        # Check for weather queries
        if any(keyword in query_lower for keyword in self.weather_keywords):
            location = self._extract_location(query) or "Sydney"
            return QueryType.WEATHER, {"location": location}
            
        # Check for time queries
        if any(keyword in query_lower for keyword in self.time_keywords):
            location = self._extract_location(query) or "Sydney"
            return QueryType.TIME, {"location": location}
            
        # Check for news queries
        if any(keyword in query_lower for keyword in self.news_keywords):
            topic = self._extract_news_topic(query)
            return QueryType.NEWS, {"topic": topic}
            
        # Check for property queries
        if any(keyword in query_lower for keyword in self.property_keywords):
            params = self._extract_property_params(query)
            # Determine if it's a search or analysis
            if any(word in query_lower for word in ["find", "search", "show", "list", "looking"]):
                return QueryType.PROPERTY_SEARCH, params
            else:
                return QueryType.PROPERTY_ANALYSIS, params
                
        # Check for calculations
        if any(keyword in query_lower for keyword in self.calculation_keywords):
            return QueryType.CALCULATION, {"expression": query}
            
        # Check if web search needed for factual questions
        if self._needs_web_search(query_lower):
            return QueryType.WEB_SEARCH, {"query": query}
            
        # Default to general chat
        return QueryType.GENERAL_CHAT, {}
        
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        # Simple greetings at start of message
        for greeting in self.greeting_keywords:
            if query.startswith(greeting):
                return True
        return False
        
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query"""
        # Common location patterns
        patterns = [
            r"in (\w+(?:\s+\w+)*)",  # "in Sydney"
            r"at (\w+(?:\s+\w+)*)",  # "at Brisbane"
            r"for (\w+(?:\s+\w+)*)",  # "for Melbourne"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1)
                # Filter out common non-location words
                if location.lower() not in ["the", "a", "an", "this", "that"]:
                    return location
        return None
        
    def _extract_news_topic(self, query: str) -> str:
        """Extract news topic from query"""
        # Remove common news-related words to find the actual topic
        topic_query = query.lower()
        for word in ["news", "latest", "current", "today's", "happening", "events", "about"]:
            topic_query = topic_query.replace(word, "")
        
        # Clean up and return
        topic = topic_query.strip()
        return topic if topic else "general"
        
    def _extract_property_params(self, query: str) -> Dict:
        """Extract property search parameters from query"""
        params = {}
        
        # Extract number of bedrooms
        bedroom_match = re.search(r"(\d+)[\s-]?(?:bed|bedroom|br)", query, re.IGNORECASE)
        if bedroom_match:
            params["bedrooms"] = int(bedroom_match.group(1))
            
        # Extract price range
        price_patterns = [
            r"\$?([\d,]+)k",  # $500k
            r"\$?([\d,]+)\s*(?:million|mil|m)",  # $2 million
            r"\$?([\d,]+)",  # $500000
            r"under\s+\$?([\d,]+)",  # under $1000000
            r"up\s+to\s+\$?([\d,]+)",  # up to $1000000
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(",", "")
                if "k" in query.lower():
                    params["max_price"] = int(price_str) * 1000
                elif any(x in query.lower() for x in ["million", "mil", "m"]):
                    params["max_price"] = int(float(price_str) * 1000000)
                else:
                    params["max_price"] = int(price_str)
                break
                
        # Extract suburb/location
        # Look for suburb names (simplified - in production would use a suburb database)
        suburbs = self._extract_suburbs(query)
        if suburbs:
            params["suburb"] = suburbs[0]  # Take first suburb mentioned
            
        # Extract property type
        property_types = {
            "house": ["house", "home"],
            "apartment": ["apartment", "unit", "flat"],
            "townhouse": ["townhouse", "town house"],
            "villa": ["villa"],
            "land": ["land", "block"]
        }
        
        for prop_type, keywords in property_types.items():
            if any(keyword in query.lower() for keyword in keywords):
                params["property_type"] = prop_type
                break
                
        return params
        
    def _extract_suburbs(self, query: str) -> List[str]:
        """Extract Sydney suburb names from query"""
        # Common Sydney suburbs (in production, would use complete database)
        sydney_suburbs = [
            "Marrickville", "Newtown", "Bondi", "Manly", "Parramatta",
            "Chatswood", "Randwick", "Surry Hills", "Paddington", "Glebe",
            "Balmain", "Leichhardt", "Stanmore", "Enmore", "Redfern",
            "Waterloo", "Alexandria", "Zetland", "Rosebery", "Mascot"
        ]
        
        found_suburbs = []
        query_lower = query.lower()
        
        for suburb in sydney_suburbs:
            if suburb.lower() in query_lower:
                found_suburbs.append(suburb)
                
        return found_suburbs
        
    def _needs_web_search(self, query: str) -> bool:
        """Determine if query needs web search for current information"""
        # Questions that typically need web search
        web_indicators = [
            "what is", "who is", "when is", "where is", "how to",
            "explain", "define", "tell me about", "latest", "current",
            "stock", "price of", "score", "game", "match"
        ]
        
        return any(indicator in query for indicator in web_indicators)
        
    def get_required_tools(self, query_type: QueryType) -> List[str]:
        """Get list of tools needed for a query type"""
        tool_mapping = {
            QueryType.WEATHER: ["tavily_search"],
            QueryType.TIME: ["datetime"],
            QueryType.NEWS: ["tavily_search"],
            QueryType.PROPERTY_SEARCH: ["property_search", "firecrawl"],
            QueryType.PROPERTY_ANALYSIS: ["ai_model", "property_data"],
            QueryType.GENERAL_CHAT: ["ai_model"],
            QueryType.GREETING: ["response_variety"],
            QueryType.CALCULATION: ["calculator"],
            QueryType.WEB_SEARCH: ["tavily_search", "ai_model"]
        }
        
        return tool_mapping.get(query_type, ["ai_model"])

# Global analyzer instance
query_analyzer = QueryAnalyzer()