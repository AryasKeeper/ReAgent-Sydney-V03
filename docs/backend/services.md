# Backend Services

This section documents public classes and functions intended for use across the backend.

## AI Router

- Class: `services.ai_router_fixed.FixedAIRouter`
- Instance: `services.ai_router_fixed.fixed_ai_router`
- Method: `process_message(message: str, session_id: str, history: List[Dict] = None) -> AsyncGenerator[str, None]`
- Purpose: Streams AI responses using OpenAI with robust error handling and model fallback (GPT-5 → GPT-4 Turbo → GPT-4 → GPT-3.5).

Usage (inside async context):
```python
from services.ai_router_fixed import fixed_ai_router

async for chunk in fixed_ai_router.process_message("Analyze the Marrickville market outlook", "session-1", []):
    print(chunk, end="")
```

### Alternative Routers

- Class: `services.ai_router.AIRouter` (Claude/GPT routing)
- Class: `services.ai_router_simple.SimpleAIRouter` (GPT-5 only)
- Instances: `ai_router`, `simple_ai_router`
- Methods: same signature as above

## Property Search

- Class: `services.property_search.PropertySearchService`
- Instance: `services.property_search.property_search`
- Method: `await search_properties(query: str) -> str`
- Strategy: Firecrawl → Tavily → Mock data. Never returns empty results.

Example:
```python
from services.property_search import property_search
text = await property_search.search_properties("3 bed houses under $2m in Marrickville")
print(text)
```

## Query Analyzer

- Enum: `services.query_analyzer.QueryType`
- Class: `services.query_analyzer.QueryAnalyzer`
- Instance: `services.query_analyzer.query_analyzer`
- Method: `analyze_query(query: str) -> tuple[QueryType, dict]`

Example:
```python
from services.query_analyzer import query_analyzer, QueryType
qt, params = query_analyzer.analyze_query("What's the weather in Sydney?")
assert qt == QueryType.WEATHER
```

## Response Variety

- Functions:
  - `get_greeting() -> str`
  - `get_search_intro() -> str`
  - `get_weather_intro() -> str`
  - `get_fallback_message() -> str`

## Session Manager

- Class: `services.session_manager.SessionManager`
- Instance: `services.session_manager.session_manager`
- Methods:
  - `should_introduce(session_id: str) -> bool`
  - `mark_introduced(session_id: str) -> None`
  - `add_message(session_id: str, role: str, content: str) -> None`
  - `get_history(session_id: str) -> list[dict]`
  - `cleanup_old_sessions(timeout_minutes: int = 30) -> None`

## Web Search

- Class: `services.web_search.WebSearchService`
- Instance: `services.web_search.web_search`
- Methods:
  - `await search_weather_time(query: str) -> str`