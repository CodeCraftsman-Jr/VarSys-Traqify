@echo off
REM Update Deployment Script for Windows
REM This script helps deploy updates to Firebase Hosting

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Personal Finance Dashboard
echo   Update Deployment Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "scripts\deploy_update.py" (
    echo ERROR: deploy_update.py not found
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Get version from user
set /p VERSION="Enter version number (e.g., 1.0.1): "
if "%VERSION%"=="" (
    echo ERROR: Version number is required
    pause
    exit /b 1
)

REM Get channel from user
echo.
echo Select release channel:
echo 1. Development (dev)
echo 2. Beta (beta)
echo 3. Stable (stable)
echo.
set /p CHANNEL_CHOICE="Enter choice (1-3): "

if "%CHANNEL_CHOICE%"=="1" set CHANNEL=dev
if "%CHANNEL_CHOICE%"=="2" set CHANNEL=beta
if "%CHANNEL_CHOICE%"=="3" set CHANNEL=stable

if "%CHANNEL%"=="" (
    echo ERROR: Invalid channel choice
    pause
    exit /b 1
)

REM Check for available builds
echo.
echo Checking for available builds...
python scripts\deploy_update.py --list-builds

echo.
set /p USE_LATEST="Use latest build? (y/n): "
if /i "%USE_LATEST%"=="n" (
    set /p EXE_PATH="Enter path to executable: "
    if not exist "!EXE_PATH!" (
        echo ERROR: Executable file not found
        pause
        exit /b 1
    )
    set EXE_ARG=--exe "!EXE_PATH!"
) else (
    set EXE_ARG=
)

REM Ask about required update
echo.
set /p IS_REQUIRED="Mark as required update? (y/n): "
if /i "%IS_REQUIRED%"=="y" (
    set REQUIRED_ARG=--required
) else (
    set REQUIRED_ARG=
)

REM Ask about deployment
echo.
set /p DEPLOY_NOW="Deploy to Firebase Hosting after packaging? (y/n): "
if /i "%DEPLOY_NOW%"=="y" (
    set DEPLOY_ARG=--deploy
) else (
    set DEPLOY_ARG=
)

REM Run the deployment script
echo.
echo ========================================
echo Deploying update %VERSION% to %CHANNEL% channel...
echo ========================================
echo.

python scripts\deploy_update.py --version "%VERSION%" --channel "%CHANNEL%" %EXE_ARG% %REQUIRED_ARG% %DEPLOY_ARG%

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo Version: %VERSION%
echo Channel: %CHANNEL%
echo.

if /i "%DEPLOY_NOW%"=="y" (
    echo The update has been deployed to Firebase Hosting.
    echo Users will receive the update notification on their next check.
) else (
    echo The update has been packaged but not deployed.
    echo Run 'firebase deploy --only hosting' to deploy manually.
)

echo.
pause
