@echo off
cd /d "D:\project\motorapi"
if errorlevel 1 exit /b 1

call .venv\Scripts\activate

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $listenerPids = @(Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); foreach ($listenerPid in $listenerPids) { Write-Host ('Stopping process {0} using port 9999' -f $listenerPid); Stop-Process -Id $listenerPid -Force }; Start-Sleep -Milliseconds 500; if (Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue) { Write-Error 'Port 9999 is still in use'; exit 1 }"
if errorlevel 1 (
    echo Failed to free port 9999. The API was not started.
    exit /b 1
)
:: Start uvicorn in the background and redirect output to server.log
start /b python -m uvicorn main:app --host 127.0.0.1 --port 9999 > server.log 2>&1

:: Wait a second for the log file to be created
timeout /t 1 /nobreak >nul

:: Tail the log file live in the console window
powershell -Command "Get-Content server.log -Wait"