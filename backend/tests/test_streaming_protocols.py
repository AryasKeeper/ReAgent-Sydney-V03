"""
Test streaming protocol support for both v3 and v5 formats
"""
import pytest
import json
from utils.streaming import format_sse_chunk, detect_protocol_version, format_v3_chunk, format_v5_chunk


class TestProtocolDetection:
    """Test protocol version detection from headers"""
    
    def test_detect_v5_with_ui_message_stream_header(self):
        headers = {"x-vercel-ai-ui-message-stream": "v1"}
        assert detect_protocol_version(headers) == "v5"
    
    def test_detect_v5_with_explicit_version_header(self):
        headers = {"x-ai-sdk-version": "5"}
        assert detect_protocol_version(headers) == "v5"
    
    def test_detect_v3_by_default(self):
        headers = {}
        assert detect_protocol_version(headers) == "v3"
    
    def test_detect_v3_with_other_headers(self):
        headers = {"content-type": "application/json", "user-agent": "test"}
        assert detect_protocol_version(headers) == "v3"


class TestV3Protocol:
    """Test v3 (legacy) protocol formatting"""
    
    def test_text_chunk_format(self):
        result = format_v3_chunk("Hello world", "text")
        assert result == '0:"Hello world"\n'
    
    def test_text_chunk_escaping(self):
        result = format_v3_chunk('Test "quotes" and \n newlines', "text")
        assert result == '0:"Test \\"quotes\\" and \\n newlines"\n'
    
    def test_finish_signal(self):
        result = format_v3_chunk("", "finish")
        assert result == 'd:{"finishReason":"stop"}\n'
    
    def test_sources_metadata(self):
        sources = ["http://example.com", "http://test.com"]
        result = format_v3_chunk(sources, "sources_meta")
        # JSON formatting may include spaces after commas
        assert result == '8:["http://example.com", "http://test.com"]\n'
    
    def test_error_format(self):
        result = format_v3_chunk("Error message", "error")
        assert result == 'd:{"finishReason":"error","error":"Error message"}\n'


class TestV5Protocol:
    """Test v5 (UI Message Stream) protocol formatting"""
    
    def test_text_delta_format(self):
        result = format_v5_chunk("Hello world", "text")
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "text-delta"
        assert parsed["textDelta"] == "Hello world"
        assert result.startswith("data: ")
        assert result.endswith("\n\n")
    
    def test_finish_signal(self):
        result = format_v5_chunk("", "finish")
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "finish"
        assert parsed["finishReason"] == "stop"
        assert "usage" in parsed
    
    def test_sources_as_tool_result(self):
        sources = ["http://example.com", "http://test.com"]
        result = format_v5_chunk(sources, "sources_meta")
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "tool-result"
        assert parsed["toolName"] == "web_search"
        assert parsed["result"] == sources
    
    def test_error_format(self):
        result = format_v5_chunk("Error message", "error")
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "error"
        assert parsed["error"]["message"] == "Error message"
        assert parsed["error"]["type"] == "stream_error"
    
    def test_message_start(self):
        result = format_v5_chunk("", "message_start")
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "message-start"
        assert "id" in parsed
        assert parsed["role"] == "assistant"


class TestProtocolSwitching:
    """Test automatic protocol switching"""
    
    def test_format_with_v3_protocol(self):
        result = format_sse_chunk("Test", "text", "v3")
        assert result == '0:"Test"\n'
    
    def test_format_with_v5_protocol(self):
        result = format_sse_chunk("Test", "text", "v5")
        assert "data: " in result
        parsed = json.loads(result.replace("data: ", "").strip())
        assert parsed["type"] == "text-delta"
        assert parsed["textDelta"] == "Test"
    
    def test_default_to_v3(self):
        result = format_sse_chunk("Test", "text")
        assert result == '0:"Test"\n'
    
    def test_finish_signal_switching(self):
        v3_finish = format_sse_chunk("", "finish", "v3")
        assert v3_finish == 'd:{"finishReason":"stop"}\n'
        
        v5_finish = format_sse_chunk("", "finish", "v5")
        assert "data: " in v5_finish
        parsed = json.loads(v5_finish.replace("data: ", "").strip())
        assert parsed["type"] == "finish"


@pytest.mark.asyncio
async def test_integration_with_headers():
    """Test integration of header detection and formatting"""
    
    # Simulate v3 request
    v3_headers = {"content-type": "application/json"}
    protocol = detect_protocol_version(v3_headers)
    chunk = format_sse_chunk("Hello", "text", protocol)
    assert chunk == '0:"Hello"\n'
    
    # Simulate v5 request
    v5_headers = {"x-vercel-ai-ui-message-stream": "v1"}
    protocol = detect_protocol_version(v5_headers)
    chunk = format_sse_chunk("Hello", "text", protocol)
    assert "data: " in chunk
    assert "text-delta" in chunk