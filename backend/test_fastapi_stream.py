"""Test FastAPI streaming directly"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio

app = FastAPI()

@app.get("/test/stream")
async def test_stream():
    async def generate():
        try:
            print("DEBUG: Generator started")
            yield '0:"Hello from test"\n'
            yield '0:" World!"\n'
            yield 'd:{"finishReason":"stop"}\n'
            print("DEBUG: Generator completed")
        except Exception as e:
            print(f"ERROR in generator: {e}")
            import traceback
            traceback.print_exc()
            yield '0:"Error occurred"\n'
            yield 'd:{"finishReason":"stop"}\n'
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    print("Starting test server on http://localhost:8001")
    print("Test with: curl http://localhost:8001/test/stream")
    uvicorn.run(app, host="0.0.0.0", port=8001)