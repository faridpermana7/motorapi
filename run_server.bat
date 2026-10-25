@echo off
cd /d "D:\project\motorapi"

set "VBOXMANAGE=C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
if not exist "%VBOXMANAGE%" (
    echo VirtualBox VBoxManage was not found: "%VBOXMANAGE%"
    exit /b 1
)

echo Checking if VirtualBox Database VM (farbuntu) is already running...
"%VBOXMANAGE%" list runningvms | findstr /i /c:"\"farbuntu\"" >nul
if errorlevel 1 (
    echo VirtualBox VM "farbuntu" is not running. Starting it now...
    "%VBOXMANAGE%" startvm "farbuntu" --type headless >nul 2>&1
    if errorlevel 1 (
        echo Failed to start VirtualBox VM "farbuntu".
        exit /b 1
    )
    echo Waiting 10 seconds for the database to initialize...
    ping 127.0.0.1 -n 11 >nul
) else (
    echo VirtualBox VM "farbuntu" is already running. Skipping startup.
)

echo Clearing port 9999...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $listenerPids = @(Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique); foreach ($listenerPid in $listenerPids) { Write-Host ('Stopping process {0} using port 9999' -f $listenerPid); Stop-Process -Id $listenerPid -Force }; Start-Sleep -Milliseconds 500; if (Get-NetTCPConnection -LocalPort 9999 -State Listen -ErrorAction SilentlyContinue) { Write-Error 'Port 9999 is still in use'; exit 1 }"
if errorlevel 1 (
    echo Failed to free port 9999. The API was not started.
    exit /b 1
)

echo Starting Uvicorn API server...
"D:\project\motorapi\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 9999 --log-config log_config.json