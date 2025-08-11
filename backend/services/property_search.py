"""Property search service with triple fallback strategy"""
import httpx
import logging
import json
import re
from typing import Optional, Dict, List
from config import settings
from utils.mock_data import get_mock_properties, format_properties_text

logger = logging.getLogger(__name__)

class PropertySearchService:
    """Handles property searches with Firecrawl → Tavily → Mock fallback"""
    
    def __init__(self):
        self.firecrawl_api_key = settings.FIRECRAWL_API_KEY
        self.tavily_api_key = settings.TAVILY_API_KEY
    
    async def search_properties(self, query: str) -> str:
        """
        Search for properties using triple fallback strategy
        Never returns empty results
        """
        logger.info(f"Property search initiated: {query}")
        
        # Extract search parameters from query
        params = self._extract_search_params(query)
        
        # Strategy 1: Try Firecrawl (if not in mock mode)
        if not settings.USE_MOCK and self.firecrawl_api_key:
            result = await self._firecrawl_search(params)
            if result:
                return result
        
        # Strategy 2: Try Tavily for market insights
        if not settings.USE_MOCK and self.tavily_api_key:
            result = await self._tavily_property_search(params)
            if result:
                return result
        
        # Strategy 3: Return high-quality mock data
        logger.info("Using mock property data")
        properties = get_mock_properties(
            suburb=params.get("suburb", "Marrickville"),
            bedrooms=params.get("bedrooms", 3),
            max_price=params.get("max_price", 2500000)
        )
        return format_properties_text(properties)
    
    def _extract_search_params(self, query: str) -> Dict:
        """Extract search parameters from natural language query"""
        params = {}
        
        # Extract suburb
        suburbs = ["marrickville", "newtown", "stanmore", "enmore", "dulwich hill", "petersham",
                   "bondi", "bondi beach", "bondi junction", "north bondi", "randwick", "coogee",
                   "manly", "mosman", "paddington", "surry hills", "alexandria", "zetland"]
        query_lower = query.lower()
        for suburb in suburbs:
            if suburb in query_lower:
                params["suburb"] = suburb.title()
                break
        
        # Extract bedrooms
        bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom)', query_lower)
        if bedroom_match:
            params["bedrooms"] = int(bedroom_match.group(1))
        
        # Extract price
        price_match = re.search(r'\$?([\d.]+)\s*(?:m|million|k|thousand)', query_lower)
        if price_match:
            price = float(price_match.group(1))
            if 'm' in query_lower or 'million' in query_lower:
                params["max_price"] = int(price * 1000000)
            elif 'k' in query_lower or 'thousand' in query_lower:
                params["max_price"] = int(price * 1000)
        
        logger.info(f"Extracted params: {params}")
        return params
    
    async def _firecrawl_search(self, params: Dict) -> Optional[str]:
        """Try to search using Firecrawl API"""
        try:
            # Build search URLs
            urls = self._build_search_urls(params)
            
            for url in urls[:1]:  # Try first URL
                from services.http_utils import fetch_with_retries, CircuitBreaker
                breaker = CircuitBreaker()
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await fetch_with_retries(
                        lambda: client.post(
                        "https://api.firecrawl.dev/v1/scrape",
                        headers={
                            "Authorization": f"Bearer {self.firecrawl_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "url": url,
                            "formats": ["markdown"],
                            "onlyMainContent": True
                        }
                    ),
                    retries=2,
                    base_delay=0.5,
                    breaker=breaker,
                    )
                    
                    if response.status_code == 200:
                        # For now, return that we found listings
                        # In production, parse the markdown for actual properties
                        return f"Found property listings in {params.get('suburb', 'Sydney')}.\n\n- {url}"
                    else:
                        logger.warning(f"Firecrawl returned {response.status_code}")
                        
        except Exception as e:
            logger.error(f"Firecrawl error: {e}")
        
        return None
    
    async def _tavily_property_search(self, params: Dict) -> Optional[str]:
        """Use Tavily to get property market insights"""
        try:
            query = f"Sydney real estate {params.get('suburb', '')} {params.get('bedrooms', '')} bedroom houses under ${params.get('max_price', 2500000)}"
            
            from services.http_utils import fetch_with_retries, CircuitBreaker
            breaker = CircuitBreaker()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await fetch_with_retries(
                    lambda: client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": True
                    }
                    ),
                    retries=2,
                    base_delay=0.5,
                    breaker=breaker,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("answer"):
                        answer = data["answer"]
                        try:
                            # Cache summary by query
                            from services.redis_store import redis_store
                            await redis_store.set_json(f"ps:tav:{query}", answer, ttl_seconds=1800)
                        except Exception:
                            pass
                        return f"Based on current market data:\n\n{answer}\n\nFor specific listings, check Domain.com.au or RealEstate.com.au"
                        
        except Exception as e:
            logger.error(f"Tavily property search error: {e}")
        
        return None
    
    def _build_search_urls(self, params: Dict) -> List[str]:
        """Build search URLs for Domain and RealEstate"""
        urls = []
        
        suburb = params.get("suburb", "marrickville").lower().replace(" ", "-")
        bedrooms = params.get("bedrooms", 3)
        max_price = params.get("max_price", 2500000)
        
        # Domain URL
        domain_url = f"https://www.domain.com.au/sale/{suburb}-nsw-2204/?bedrooms={bedrooms}-any&price=0-{max_price}"
        urls.append(domain_url)
        
        # RealEstate URL
        re_url = f"https://www.realestate.com.au/buy/with-{bedrooms}-bedrooms-between-0-{max_price}-in-{suburb},+nsw+2204/list-1"
        urls.append(re_url)
        
        return urls

# Global property search instance
property_search = PropertySearchService()