"""
Enhanced Query Analyzer with Prioritized Classification
Implements explicit web search override with negation handling and session memory
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta

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


class ClassificationLogger:
    """Rate-limited, safe classification logging."""
    
    def __init__(self):
        self.log_counts = {}
        self.last_reset = datetime.now()
        self.rate_limit = 100  # Max logs per minute
        self.max_query_length = 50
    
    def log_classification(self, reason: str, query: str):
        """Log classification with rate limiting and sanitization."""
        
        # Reset counts every minute
        if (datetime.now() - self.last_reset).seconds > 60:
            self.log_counts = {}
            self.last_reset = datetime.now()
        
        # Check rate limit
        current_count = self.log_counts.get(reason, 0)
        if current_count >= self.rate_limit:
            return
        
        # Sanitize and truncate query
        safe_query = query[:self.max_query_length].replace('\n', ' ').replace('\r', '')
        
        # Bucket by length
        if len(query) > 100:
            query_bucket = "long_query"
        elif len(query) > 50:
            query_bucket = "medium_query"
        else:
            query_bucket = "short_query"
        
        logger.info(f"Classification: {reason} | Bucket: {query_bucket} | Sample: {safe_query}...")
        self.log_counts[reason] = current_count + 1


class QueryAnalyzer:
    """Analyzes user queries to determine intent and required tools"""
    
    def __init__(self):
        # Initialize classification logger
        self.classification_logger = ClassificationLogger()
        
        # Session preferences storage
        self.session_preferences = {}  # {session_id: {"force_web": bool, "timestamp": datetime}}
        
        # Explicit web search triggers (highest priority)
        self.explicit_web_triggers = [
            # Core triggers
            "use live sources", "live sources", "use web", "browse the web",
            "browse web", "browse the internet", "browse internet",
            "search online", "search the internet", "search the web",
            "from the web", "from the internet", "from web", "from internet",
            
            # Time-based triggers
            "real-time", "real time", "realtime", "up-to-date", "up to date",
            "latest information", "current information", "most recent",
            "latest", "current", "newest", "recent",
            "today's", "todays", "right now", "this moment",
            
            # Additional aliases
            "latest from the web", "latest from web", "pull from web", "pull from the web",
            "real time data", "realtime data", "live data", "fresh data",
            "source links", "with sources", "citations", "with citations",
            "cite sources", "provide sources", "fetch from internet",
            "get from web", "retrieve online", "updated information",
            "search for", "look up online", "check online", "find online"
        ]
        
        # Negation patterns
        self.negation_patterns = [
            "don't", "dont", "do not", "no need", "without",
            "skip", "avoid", "not", "shouldn't", "shouldnt",
            "never", "stop", "disable", "turn off", "no",
            "instead of", "rather than", "except"
        ]
        
        # Domain-specific keywords
        self.weather_keywords = ["weather", "temperature", "rain", "sunny", "cloudy", 
                                "forecast", "hot", "cold", "humid", "storm"]
        self.time_keywords = ["time", "clock", "hour", "what time", "current time", "timezone"]
        self.news_keywords = ["news", "happening", "events", "headlines", "breaking"]
        self.property_keywords = ["property", "house", "apartment", "bedroom", "real estate", 
                                 "buy", "sell", "rent", "sale", "price", "suburb", "home",
                                 "unit", "townhouse", "villa", "land", "auction", "listing"]
        self.greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", 
                                "good evening", "how are you", "what's up", "greetings"]
        self.calculation_keywords = ["calculate", "compute", "solve", "math", "+", "-", "*", "/", "="]
        
        # Implicit web search indicators (lower priority)
        self.implicit_web_indicators = [
            "what is", "who is", "when is", "where is", "how to",
            "explain", "define", "tell me about", "latest", "current",
            "stock", "price of", "score", "game", "match",
            "what are the current", "what's happening", "recent updates"
        ]
    
    def _check_session_preference(self, session_id: str, query: str) -> Optional[QueryType]:
        """Check and update session preferences for web search."""
        query_lower = query.lower()
        
        # Check for preference commands
        if "always use live sources" in query_lower or "always use web" in query_lower:
            self.session_preferences[session_id] = {
                "force_web": True,
                "timestamp": datetime.now()
            }
            logger.info(f"Session {session_id}: Enabled persistent web search")
            return QueryType.WEB_SEARCH
        
        if "stop using live sources" in query_lower or "stop using web" in query_lower:
            if session_id in self.session_preferences:
                del self.session_preferences[session_id]
            logger.info(f"Session {session_id}: Disabled persistent web search")
            return QueryType.GENERAL_CHAT
        
        # Check existing preference
        session_pref = self.session_preferences.get(session_id, {})
        if session_pref.get("force_web"):
            # Check if preference is still valid (30 minute timeout)
            if (datetime.now() - session_pref["timestamp"]).seconds < 1800:
                logger.info(f"Session {session_id}: Using persistent web search preference")
                return QueryType.WEB_SEARCH
            else:
                # Expired preference
                del self.session_preferences[session_id]
        
        return None
    
    def _is_explicit_web_search(self, query: str) -> bool:
        """Check for explicit web search instructions with proximity-based negation."""
        
        # Check each trigger
        for trigger in self.explicit_web_triggers:
            if trigger in query:
                trigger_pos = query.find(trigger)
                
                # Look for negations that might apply to this trigger
                # Check text before the trigger for negations
                before_text = query[:trigger_pos].lower()
                
                # Common negation patterns that apply to following phrases
                negation_phrases = [
                    "don't", "dont", "do not", "no need to", "without",
                    "skip", "avoid", "shouldn't", "shouldnt", "never"
                ]
                
                # Check if any negation appears close before the trigger
                for neg in negation_phrases:
                    if neg in before_text:
                        # Check if negation is within reasonable distance (last 50 chars)
                        neg_pos = before_text.rfind(neg)
                        if trigger_pos - neg_pos < 50:
                            # Check for intervening punctuation that might separate clauses
                            intervening = query[neg_pos + len(neg):trigger_pos]
                            # If there's a comma or "but", the negation might not apply
                            if ", but" not in intervening and ", and" not in intervening:
                                logger.info(f"Negation '{neg}' blocks trigger '{trigger}'")
                                return False
                
                logger.info(f"Explicit web trigger found: '{trigger}'")
                return True
        
        return False
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        for greeting in self.greeting_keywords:
            if query.startswith(greeting):
                return True
        return False
    
    def _needs_implicit_web_search(self, query: str) -> bool:
        """Check for implicit web search needs (lower priority)"""
        return any(indicator in query for indicator in self.implicit_web_indicators)
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query"""
        patterns = [
            r"in (\w+(?:\s+\w+)*)",
            r"at (\w+(?:\s+\w+)*)",
            r"for (\w+(?:\s+\w+)*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                location = match.group(1)
                if location.lower() not in ["the", "a", "an", "this", "that"]:
                    return location
        return None
    
    def _extract_news_topic(self, query: str) -> str:
        """Extract news topic from query"""
        topic_query = query.lower()
        for word in ["news", "latest", "current", "today's", "happening", "events", "about"]:
            topic_query = topic_query.replace(word, "")
        
        topic = topic_query.strip()
        return topic if topic else "general"
    
    def _extract_property_params(self, query: str) -> Dict:
        """Extract property search parameters from query"""
        params = {}
        
        # Extract bedrooms
        bedroom_match = re.search(r"(\d+)[\s-]?(?:bed|bedroom|br)", query, re.IGNORECASE)
        if bedroom_match:
            params["bedrooms"] = int(bedroom_match.group(1))
        
        # Extract price
        price_patterns = [
            r"\$?([\d,]+)k",
            r"\$?([\d,]+)\s*(?:million|mil|m)",
            r"\$?([\d,]+)",
            r"under\s+\$?([\d,]+)",
            r"up\s+to\s+\$?([\d,]+)",
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
        
        # Extract suburbs
        suburbs = self._extract_suburbs(query)
        if suburbs:
            params["suburb"] = suburbs[0]
        
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
    
    def analyze_query(self, query: str, session_id: str = "default") -> Tuple[QueryType, Dict]:
        """
        Analyze a query with prioritized classification.
        Priority: Session prefs > Explicit web > Greeting > Domain > Implicit web > General
        """
        query_lower = query.lower()
        classification_reason = None
        
        # PRIORITY 0: Check session preferences
        session_type = self._check_session_preference(session_id, query)
        if session_type:
            classification_reason = "session_preference"
            self.classification_logger.log_classification(classification_reason, query)
            return session_type, {"query": query, "session_forced": True}
        
        # PRIORITY 1: Check for explicit web search (with negation handling)
        if self._is_explicit_web_search(query_lower):
            classification_reason = "explicit_web_search"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.WEB_SEARCH, {"query": query}
        
        # PRIORITY 2: Check for greetings
        if self._is_greeting(query_lower):
            classification_reason = "greeting"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.GREETING, {}
        
        # PRIORITY 3: Domain-specific checks
        
        # Weather
        if any(keyword in query_lower for keyword in self.weather_keywords):
            location = self._extract_location(query) or "Sydney"
            classification_reason = "weather_domain"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.WEATHER, {"location": location}
        
        # Time
        if any(keyword in query_lower for keyword in self.time_keywords):
            location = self._extract_location(query) or "Sydney"
            classification_reason = "time_domain"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.TIME, {"location": location}
        
        # News
        if any(keyword in query_lower for keyword in self.news_keywords):
            topic = self._extract_news_topic(query)
            classification_reason = "news_domain"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.NEWS, {"topic": topic}
        
        # Property
        if any(keyword in query_lower for keyword in self.property_keywords):
            params = self._extract_property_params(query)
            if any(word in query_lower for word in ["find", "search", "show", "list", "looking"]):
                classification_reason = "property_search"
                self.classification_logger.log_classification(classification_reason, query)
                return QueryType.PROPERTY_SEARCH, params
            else:
                classification_reason = "property_analysis"
                self.classification_logger.log_classification(classification_reason, query)
                return QueryType.PROPERTY_ANALYSIS, params
        
        # Calculation
        if any(keyword in query_lower for keyword in self.calculation_keywords):
            classification_reason = "calculation"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.CALCULATION, {"expression": query}
        
        # PRIORITY 4: Implicit web search (fallback)
        if self._needs_implicit_web_search(query_lower):
            classification_reason = "implicit_web_search"
            self.classification_logger.log_classification(classification_reason, query)
            return QueryType.WEB_SEARCH, {"query": query}
        
        # DEFAULT: General chat
        classification_reason = "general_fallback"
        self.classification_logger.log_classification(classification_reason, query)
        return QueryType.GENERAL_CHAT, {}
    
    def analyze_query_with_fallback(self, query: str, session_id: str, 
                                   has_web_apis: bool) -> Tuple[QueryType, Dict, Optional[str]]:
        """Analyze with safe fallback when services unavailable."""
        
        query_type, params = self.analyze_query(query, session_id)
        fallback_notice = None
        
        # If WEB_SEARCH but missing required services
        if query_type == QueryType.WEB_SEARCH and not has_web_apis:
            original_type = query_type
            
            # Find best fallback based on query content
            query_lower = query.lower()
            
            if any(kw in query_lower for kw in self.property_keywords):
                query_type = QueryType.PROPERTY_SEARCH
                params = self._extract_property_params(query)
                fallback_notice = "Note: Live sources unavailable, using cached property data."
            elif any(kw in query_lower for kw in self.weather_keywords):
                query_type = QueryType.WEATHER
                params = {"location": self._extract_location(query) or "Sydney"}
                fallback_notice = "Note: Live sources unavailable, using weather service."
            elif any(kw in query_lower for kw in self.news_keywords):
                query_type = QueryType.NEWS
                params = {"topic": self._extract_news_topic(query)}
                fallback_notice = "Note: Live sources unavailable, using cached news."
            else:
                query_type = QueryType.GENERAL_CHAT
                params = {}
                fallback_notice = "Note: Live sources unavailable, using AI knowledge base."
            
            logger.warning(f"Fallback from {original_type} to {query_type} - missing APIs")
        
        return query_type, params, fallback_notice
    
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
            QueryType.WEB_SEARCH: ["brave_search", "firecrawl", "ai_model"]
        }
        
        return tool_mapping.get(query_type, ["ai_model"])

# Global analyzer instance
query_analyzer = QueryAnalyzer()