@echo off
echo Starting backend server with debug output...
start cmd /k "python app.py"
timeout /t 3 >nul
echo.
echo Testing chat endpoint...
curl -X POST http://localhost:8000/api/v1/agent-whisperer/chat/stream -H "Content-Type: application/json" -d "{\"message\":\"Hello\",\"session_id\":\"test-debug\",\"messages\":[]}"
echo.
echo Check the backend window for debug output!