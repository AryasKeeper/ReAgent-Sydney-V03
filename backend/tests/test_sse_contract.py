import pytest
import httpx


@pytest.mark.asyncio
async def test_chat_sse_contract():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001", timeout=None) as client:
        r = await client.post(
            "/api/v1/agent-whisperer/chat/stream",
            json={"message": "hello", "session_id": "test"},
        )
        assert r.status_code == 200
        got_text = False
        got_finish = False
        async for line in r.aiter_lines():
            if not line:
                continue
            if line.startswith("0:"):
                got_text = True
            if line == 'd:{"finishReason":"stop"}':
                got_finish = True
                break
        assert got_text and got_finish


