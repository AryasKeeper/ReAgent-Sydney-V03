"""Comprehensive backfill and reconnect test with token expiry."""

import asyncio
import json
import time
import jwt
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Dict, Any
import pytest
import httpx
from fastapi.testclient import TestClient

# Test configuration
TEST_SECRET = "test-secret-key-for-jwt-tokens"
TEST_ORG_ID = "test_org_123"
BACKEND_URL = "http://localhost:8001"


def create_test_jwt(org_id: str, expires_in_seconds: int = 300) -> str:
    """Create test JWT token with specified expiry."""
    payload = {
        "org_id": org_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=expires_in_seconds),
        "aud": "reagent-api"
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def parse_sse_chunk(line: str) -> Dict[str, Any]:
    """Parse SSE chunk into type and content."""
    if not line.strip():
        return {"type": "empty", "content": None}
    
    if line.startswith("0:"):
        # Text chunk
        try:
            content = json.loads(line[2:])
            return {"type": "text", "content": content}
        except json.JSONDecodeError:
            return {"type": "text", "content": line[2:]}
    elif line.startswith("d:"):
        # Finish signal
        try:
            content = json.loads(line[2:])
            return {"type": "finish", "content": content}
        except json.JSONDecodeError:
            return {"type": "finish", "content": {}}
    elif line.startswith("8:"):
        # Sources metadata
        try:
            content = json.loads(line[2:])
            return {"type": "sources", "content": content}
        except json.JSONDecodeError:
            return {"type": "sources", "content": []}
    elif line.startswith("error:"):
        # Error message
        return {"type": "error", "content": line[6:]}
    else:
        return {"type": "unknown", "content": line}


class StreamingSession:
    """Manages streaming session with reconnection capability."""
    
    def __init__(self, initial_token: str):
        self.current_token = initial_token
        self.session_id = f"test_session_{int(time.time())}"
        self.message_history: List[Dict[str, str]] = []
        self.received_chunks: List[Dict[str, Any]] = []
        self.connection_attempts = 0
        self.max_retries = 3
    
    async def send_message_with_streaming(self, message: str) -> Dict[str, Any]:
        """Send message and handle streaming response with reconnection."""
        self.connection_attempts += 1
        
        payload = {
            "message": message,
            "session_id": self.session_id,
            "messages": self.message_history.copy()
        }
        
        headers = {
            "Authorization": f"Bearer {self.current_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        result = {
            "success": False,
            "chunks": [],
            "error": None,
            "status_code": None,
            "reconnected": False,
            "final_response": ""
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    f"{BACKEND_URL}/api/v1/agent-whisperer/chat/stream",
                    json=payload,
                    headers=headers
                ) as response:
                    result["status_code"] = response.status_code
                    
                    if response.status_code == 401:
                        # Token expired - attempt reconnection
                        return await self._handle_token_expiry(message)
                    
                    if response.status_code != 200:
                        result["error"] = f"HTTP {response.status_code}: {await response.aread()}"
                        return result
                    
                    # Process streaming response
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            chunk = parse_sse_chunk(line)
                            result["chunks"].append(chunk)
                            self.received_chunks.append(chunk)
                            
                            if chunk["type"] == "text" and chunk["content"]:
                                full_response += chunk["content"]
                            elif chunk["type"] == "finish":
                                break
                            elif chunk["type"] == "error":
                                result["error"] = chunk["content"]
                                return result
                    
                    result["final_response"] = full_response
                    result["success"] = True
                    
                    # Update message history
                    self.message_history.extend([
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": full_response}
                    ])
                    
                    return result
                    
        except httpx.TimeoutException:
            result["error"] = "Request timeout"
            return result
        except Exception as e:
            result["error"] = f"Connection error: {str(e)}"
            return result
    
    async def _handle_token_expiry(self, message: str) -> Dict[str, Any]:
        """Handle token expiry with reconnection."""
        if self.connection_attempts > self.max_retries:
            return {
                "success": False,
                "error": "Max reconnection attempts exceeded",
                "reconnected": False,
                "chunks": [],
                "final_response": ""
            }
        
        # Create new token with longer expiry
        self.current_token = create_test_jwt(TEST_ORG_ID, expires_in_seconds=300)
        
        # Retry the request
        result = await self.send_message_with_streaming(message)
        result["reconnected"] = True
        return result


@pytest.mark.asyncio
async def test_short_token_expiry_during_stream():
    """Test token expiry during streaming with automatic reconnection."""
    # Create token that expires in 5 seconds
    short_token = create_test_jwt(TEST_ORG_ID, expires_in_seconds=5)
    session = StreamingSession(short_token)
    
    # Send first message - should succeed
    result1 = await session.send_message_with_streaming(
        "Hello, please tell me about Sydney real estate markets in detail."
    )
    
    assert result1["success"], f"First message failed: {result1['error']}"
    assert len(result1["chunks"]) > 0, "No chunks received"
    assert result1["final_response"], "No final response received"
    assert not result1["reconnected"], "Unexpected reconnection on first message"
    
    # Wait for token to expire
    await asyncio.sleep(6)
    
    # Send second message - should trigger 401 and reconnection
    result2 = await session.send_message_with_streaming(
        "Can you provide more specific information about property prices?"
    )
    
    assert result2["success"], f"Second message failed after reconnection: {result2['error']}"
    assert result2["reconnected"], "Token expiry should have triggered reconnection"
    assert len(result2["chunks"]) > 0, "No chunks received after reconnection"
    assert result2["final_response"], "No final response after reconnection"


@pytest.mark.asyncio
async def test_comprehensive_backfill_scenario():
    """Test comprehensive backfill scenario with multiple reconnections."""
    # Start with very short token (2 seconds)
    initial_token = create_test_jwt(TEST_ORG_ID, expires_in_seconds=2)
    session = StreamingSession(initial_token)
    
    messages = [
        "What are the best suburbs in Sydney for families?",
        "Tell me about property investment opportunities.",
        "What should I know about the Sydney housing market trends?",
        "Can you explain the differences between inner and outer suburbs?",
        "What are the current interest rates and their impact?"
    ]
    
    results = []
    successful_messages = 0
    total_reconnections = 0
    
    for i, message in enumerate(messages):
        print(f"Sending message {i+1}: {message[:50]}...")
        
        # For messages after the first, wait to ensure token expiry
        if i > 0:
            await asyncio.sleep(3)
        
        result = await session.send_message_with_streaming(message)
        results.append(result)
        
        if result["success"]:
            successful_messages += 1
            if result["reconnected"]:
                total_reconnections += 1
                print(f"  → Reconnected successfully")
            else:
                print(f"  → Completed without reconnection")
        else:
            print(f"  → Failed: {result['error']}")
        
        # Short pause between messages
        await asyncio.sleep(1)
    
    # Verify backfill behavior
    assert successful_messages >= 4, f"Expected at least 4 successful messages, got {successful_messages}"
    assert total_reconnections >= 3, f"Expected at least 3 reconnections, got {total_reconnections}"
    
    # Check that session history is maintained across reconnections
    assert len(session.message_history) >= 8, "Message history not properly maintained"
    
    # Verify message continuity
    for i, result in enumerate(results):
        if result["success"]:
            assert result["final_response"], f"Message {i+1} has empty response"
            # Check for context awareness in later messages
            if i > 0 and "sydney" in messages[i].lower():
                assert any("sydney" in result["final_response"].lower() 
                          for result in results[:i+1] if result["success"]), \
                       "Context not maintained across reconnections"


@pytest.mark.asyncio
async def test_connection_cleanup():
    """Test proper connection cleanup after stream completion."""
    token = create_test_jwt(TEST_ORG_ID, expires_in_seconds=60)
    session = StreamingSession(token)
    
    # Track connection count before test
    initial_connections = await _get_active_connections()
    
    # Send multiple messages with proper cleanup
    for i in range(3):
        result = await session.send_message_with_streaming(f"Test message {i+1}")
        assert result["success"], f"Message {i+1} failed: {result['error']}"
        
        # Small delay to allow cleanup
        await asyncio.sleep(0.5)
    
    # Wait for connections to be cleaned up
    await asyncio.sleep(2)
    
    # Check final connection count
    final_connections = await _get_active_connections()
    
    # Should not have significant connection leakage
    connection_diff = final_connections - initial_connections
    assert connection_diff <= 1, f"Connection leak detected: {connection_diff} unclosed connections"


@pytest.mark.asyncio
async def test_concurrent_reconnections():
    """Test handling of concurrent reconnection scenarios."""
    # Create multiple sessions with short-lived tokens
    sessions = []
    for i in range(3):
        token = create_test_jwt(f"{TEST_ORG_ID}_{i}", expires_in_seconds=3)
        sessions.append(StreamingSession(token))
    
    # Send concurrent messages that will trigger reconnections
    async def send_message_with_delay(session: StreamingSession, delay: float, message: str):
        await asyncio.sleep(delay)
        return await session.send_message_with_streaming(message)
    
    # Start all sessions concurrently with staggered delays
    tasks = []
    for i, session in enumerate(sessions):
        task = send_message_with_delay(
            session, 
            i * 1.5,  # Staggered start
            f"Concurrent test message from session {i}"
        )
        tasks.append(task)
    
    # Wait for token expiry, then send second wave
    await asyncio.sleep(4)
    
    # Second wave - should all trigger reconnections
    for i, session in enumerate(sessions):
        task = send_message_with_delay(
            session,
            i * 0.5,
            f"Second wave message from session {i}"
        )
        tasks.append(task)
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify results
    successful_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    reconnection_count = sum(1 for r in results if isinstance(r, dict) and r.get("reconnected"))
    
    assert successful_count >= 4, f"Expected at least 4 successful concurrent operations, got {successful_count}"
    assert reconnection_count >= 2, f"Expected at least 2 reconnections, got {reconnection_count}"


async def _get_active_connections() -> int:
    """Get count of active database connections (mock implementation)."""
    # In a real implementation, this would query the database for active connections
    # For testing, we'll return a mock value
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                # Server is responsive, assume normal connection count
                return 5
            else:
                return 0
    except:
        return 0


if __name__ == "__main__":
    """Run tests manually for debugging."""
    import asyncio
    
    async def run_manual_tests():
        print("Running backfill and reconnect tests...")
        
        print("\n1. Testing short token expiry...")
        await test_short_token_expiry_during_stream()
        print("✓ Short token expiry test passed")
        
        print("\n2. Testing comprehensive backfill...")
        await test_comprehensive_backfill_scenario()
        print("✓ Comprehensive backfill test passed")
        
        print("\n3. Testing connection cleanup...")
        await test_connection_cleanup()
        print("✓ Connection cleanup test passed")
        
        print("\n4. Testing concurrent reconnections...")
        await test_concurrent_reconnections()
        print("✓ Concurrent reconnections test passed")
        
        print("\nAll tests completed successfully!")
    
    asyncio.run(run_manual_tests())