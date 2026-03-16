@echo off
cd /d %~dp0
echo ==========================================
echo Starting Roadbook Backend Server...
echo Address: http://localhost:8679
echo ==========================================

:: 启动 Uvicorn，开启 reload 便于开发时自动重启
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8679 --reload

pause
