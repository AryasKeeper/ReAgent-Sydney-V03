"""Test SSE streaming format"""
import pytest
from utils.streaming import format_sse_chunk

def test_text_chunk_format():
    """Test that text chunks are formatted correctly"""
    result = format_sse_chunk("Hello world")
    assert result == '0:"Hello world"\n'
    
    # Test with special characters
    result = format_sse_chunk('Test with "quotes" and \n newlines')
    assert result.startswith('0:')
    assert result.endswith('\n')
    assert '\\"' in result  # Quotes should be escaped

def test_finish_chunk_format():
    """Test that finish signal is formatted correctly"""
    result = format_sse_chunk("", "finish")
    assert result == 'd:{"finishReason":"stop"}\n'

def test_error_chunk_format():
    """Test that error signal is formatted correctly"""
    result = format_sse_chunk("Error message", "error")
    assert result == 'd:{"finishReason":"error","error":"Error message"}\n'

def test_invalid_chunk_type():
    """Test that invalid chunk type raises error"""
    with pytest.raises(ValueError):
        format_sse_chunk("test", "invalid")