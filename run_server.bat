@echo off
cd /d "D:\project\motorapi"
call .venv\Scripts\activate

:: Start uvicorn in the background and redirect output to server.log
start /b python -m uvicorn main:app --host 127.0.0.1 --port 9999 > server.log 2>&1

:: Wait a second for the log file to be created
timeout /t 1 /nobreak >nul

:: Tail the log file live in the console window
powershell -Command "Get-Content server.log -Wait"