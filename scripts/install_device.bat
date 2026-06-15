@echo off
REM CDLAID Device Agent Installer for Windows
REM Installs the device agent as a Windows scheduled task
REM Run as Administrator
REM Usage: install_device.bat SCHOOL_ID SERVER_ID API_KEY

echo.
echo CDLAID Device Agent Installer
echo ==============================
echo.

REM ------------------------------------------------------------
REM Check for Administrator privileges
REM ------------------------------------------------------------

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click install_device.bat and select Run as Administrator
    pause
    exit /b 1
)

REM ------------------------------------------------------------
REM Collect configuration
REM ------------------------------------------------------------

set /p SCHOOL_ID="Enter School ID (e.g. ET-AA-001): "
set /p SERVER_ID="Enter Server ID (e.g. SRV-ET-AA-001-001): "
set /p DEVICE_ID="Enter Device ID (e.g. DEV-ET-AA-001-000001): "
set /p SCHOOL_API_KEY="Enter School API Key: "

echo.
echo Configuration:
echo   School ID:  %SCHOOL_ID%
echo   Server ID:  %SERVER_ID%
echo   Device ID:  %DEVICE_ID%
echo.

REM ------------------------------------------------------------
REM Check Python is installed
REM ------------------------------------------------------------

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Download Python 3.12 from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install
    pause
    exit /b 1
)

echo Python found:
python --version

REM ------------------------------------------------------------
REM Install required Python packages
REM ------------------------------------------------------------

echo.
echo Installing required packages
pip install requests --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install required packages
    pause
    exit /b 1
)
echo Packages installed

REM ------------------------------------------------------------
REM Create installation directory
REM ------------------------------------------------------------

echo.
echo Creating installation directory

if not exist "C:\cdlaid" mkdir "C:\cdlaid"
if not exist "C:\cdlaid\logs" mkdir "C:\cdlaid\logs"

echo Directory created: C:\cdlaid

REM ------------------------------------------------------------
REM Copy device agent to installation directory
REM ------------------------------------------------------------

echo.
echo Copying device agent

copy /Y "edge\device_agent.py" "C:\cdlaid\device_agent.py" >nul
if %errorlevel% neq 0 (
    echo ERROR: Could not copy device_agent.py
    echo Make sure you are running this from the project root directory
    pause
    exit /b 1
)

echo Device agent copied to C:\cdlaid\device_agent.py

REM ------------------------------------------------------------
REM Write environment configuration file
REM ------------------------------------------------------------

echo.
echo Writing configuration

(
echo SCHOOL_ID=%SCHOOL_ID%
echo SERVER_ID=%SERVER_ID%
echo DEVICE_ID=%DEVICE_ID%
echo SCHOOL_API_KEY=%SCHOOL_API_KEY%
echo RECEIVER_URL=http://10.42.0.1:8000/api/v1/device/ingest
echo HOTSPOT_IP=10.42.0.1
echo SYNC_INTERVAL_SECONDS=60
echo SYNC_BATCH_SIZE=200
echo DEVICE_QUEUE_PATH=C:\cdlaid\device_queue.db
) > "C:\cdlaid\device_agent.env"

echo Configuration written to C:\cdlaid\device_agent.env

REM ------------------------------------------------------------
REM Write wrapper script that loads env and runs agent
REM ------------------------------------------------------------

echo.
echo Writing launcher script

(
echo @echo off
echo REM CDLAID Device Agent Launcher
echo REM Loads environment variables and starts agent
echo for /f "tokens=1,2 delims==" %%%%a in ^(C:\cdlaid\device_agent.env^) do set %%%%a=%%%%b
echo python C:\cdlaid\device_agent.py ^>^> C:\cdlaid\logs\device_agent.log 2^>^&1
) > "C:\cdlaid\run_agent.bat"

echo Launcher written to C:\cdlaid\run_agent.bat

REM ------------------------------------------------------------
REM Register as Windows Scheduled Task
REM Runs at startup and every 5 minutes
REM ------------------------------------------------------------

echo.
echo Registering scheduled task

schtasks /delete /tn "CDLAID_DeviceAgent" /f >nul 2>&1

schtasks /create ^
    /tn "CDLAID_DeviceAgent" ^
    /tr "C:\cdlaid\run_agent.bat" ^
    /sc onstart ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f

if %errorlevel% neq 0 (
    echo ERROR: Failed to register scheduled task
    pause
    exit /b 1
)

echo Scheduled task registered: CDLAID_DeviceAgent

REM ------------------------------------------------------------
REM Start the agent now without waiting for reboot
REM ------------------------------------------------------------

echo.
echo Starting agent now

schtasks /run /tn "CDLAID_DeviceAgent"
if %errorlevel% neq 0 (
    echo WARNING: Could not start agent immediately
    echo Agent will start automatically on next reboot
) else (
    echo Agent started successfully
)

REM ------------------------------------------------------------
REM Verify installation
REM ------------------------------------------------------------

echo.
echo Verifying installation

if exist "C:\cdlaid\device_agent.py" (
    echo   device_agent.py    OK
) else (
    echo   device_agent.py    MISSING
)

if exist "C:\cdlaid\device_agent.env" (
    echo   device_agent.env   OK
) else (
    echo   device_agent.env   MISSING
)

if exist "C:\cdlaid\run_agent.bat" (
    echo   run_agent.bat      OK
) else (
    echo   run_agent.bat      MISSING
)

schtasks /query /tn "CDLAID_DeviceAgent" >nul 2>&1
if %errorlevel% equ 0 (
    echo   Scheduled task     OK
) else (
    echo   Scheduled task     MISSING
)

echo.
echo ==============================
echo Installation complete
echo ==============================
echo   School ID:    %SCHOOL_ID%
echo   Device ID:    %DEVICE_ID%
echo   Queue:        C:\cdlaid\device_queue.db
echo   Logs:         C:\cdlaid\logs\device_agent.log
echo   Task name:    CDLAID_DeviceAgent
echo ==============================
echo.
echo The agent will sync automatically when connected to
echo the school hotspot Camara-%SCHOOL_ID%
echo.

pause