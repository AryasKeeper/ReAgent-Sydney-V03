# Backend Utilities

## Streaming

- Function: `utils.streaming.format_sse_chunk(content: str, chunk_type: str = "text") -> str`
- Supported `chunk_type` values: `"text"`, `"finish"`, `"error"`

Example:
```python
from utils.streaming import format_sse_chunk

print(format_sse_chunk("Hello"))            # 0:"Hello"\n
print(format_sse_chunk("", "finish"))     # d:{"finishReason":"stop"}\n
print(format_sse_chunk("Oops", "error"))  # d:{"finishReason":"error","error":"Oops"}\n
```

## Logging

- Function: `utils.logging.setup_logging(level=logging.INFO)`

Example:
```python
from utils.logging import setup_logging
logger = setup_logging()
logger.info("Ready")
```

## Mock Data

- Function: `utils.mock_data.get_mock_properties(suburb: str = "Marrickville", bedrooms: int = 3, max_price: int = 2500000) -> list[dict]`
- Function: `utils.mock_data.format_properties_text(properties: list[dict]) -> str`

Example:
```python
from utils.mock_data import get_mock_properties, format_properties_text

props = get_mock_properties("Marrickville", 3, 2000000)
print(format_properties_text(props))
```