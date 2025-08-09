"""Business logic services for ReAgent Backend V3"""

from .ai_router import ai_router  # Import the singleton instance
from .session_manager import SessionManager
from .web_search import WebSearchService
from .property_search import property_search
from .response_variety import get_greeting, get_search_intro

# Create service instances
session_manager = SessionManager()
web_search = WebSearchService()

__all__ = [
    'ai_router',
    'session_manager', 
    'web_search',
    'property_search',
    'get_greeting',
    'get_search_intro'
]