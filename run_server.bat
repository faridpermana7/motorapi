@echo off
cd /d "D:\project\motorapi"

echo Starting VirtualBox Database VM (farbuntu)...
"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" startvm "farbuntu" --type headless >nul 2>&1

echo Waiting 10 seconds for the database to initialize...
timeout /t 10 /nobreak >nul

if errorlevel 1 exit /b 1
call .venv\Scripts\activate

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $listenerPids = @(Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); foreach ($listenerPid in $listenerPids) { Write-Host ('Stopping process {0} using port 9999' -f $listenerPid); Stop-Process -Id $listenerPid -Force }; Start-Sleep -Milliseconds 500; if (Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue) { Write-Error 'Port 9999 is still in use'; exit 1 }"
if errorlevel 1 (
    echo Failed to free port 9999. The API was not started.
    exit /b 1
)

echo Starting Uvicorn API server...
python -m uvicorn main:app --host 127.0.0.1 --port 9999 --log-config log_config.json