@echo off
title Sanad Backend Server
cd /d "%~dp0backend"
echo Starting Sanad FastAPI Backend...
.venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
pause

