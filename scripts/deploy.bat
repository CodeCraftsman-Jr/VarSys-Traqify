@echo off
REM Deployment Script for Personal Finance Dashboard
REM Windows Batch Script

echo.
echo ========================================
echo Personal Finance Dashboard - Deployment
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or later
    pause
    exit /b 1
)

REM Change to project root directory
cd /d "%~dp0\.."

echo Current directory: %CD%
echo.

REM Show menu
:menu
echo Choose deployment option:
echo 1. Check prerequisites only
echo 2. Test backend locally
echo 3. Prepare Replit deployment
echo 4. Prepare Render deployment
echo 5. Prepare Appwrite Functions deployment
echo 6. Prepare all platforms
echo 7. Generate deployment checklist
echo 8. Full deployment preparation (test + all platforms + checklist)
echo 0. Exit
echo.

set /p choice="Enter your choice (0-8): "

if "%choice%"=="0" goto exit
if "%choice%"=="1" goto check
if "%choice%"=="2" goto test
if "%choice%"=="3" goto replit
if "%choice%"=="4" goto render
if "%choice%"=="5" goto appwrite
if "%choice%"=="6" goto all
if "%choice%"=="7" goto checklist
if "%choice%"=="8" goto full

echo Invalid choice. Please try again.
echo.
goto menu

:check
echo.
echo Running prerequisites check...
python scripts\deploy_manager.py --check
goto end

:test
echo.
echo Running local tests...
python scripts\deploy_manager.py --test --check
goto end

:replit
echo.
echo Preparing Replit deployment...
python scripts\deploy_manager.py --platform replit
goto end

:render
echo.
echo Preparing Render deployment...
python scripts\deploy_manager.py --platform render
goto end

:appwrite
echo.
echo Preparing Appwrite Functions deployment...
python scripts\deploy_manager.py --platform appwrite
goto end

:all
echo.
echo Preparing deployment for all platforms...
python scripts\deploy_manager.py --platform all
goto end

:checklist
echo.
echo Generating deployment checklist...
python scripts\deploy_manager.py --checklist
goto end

:full
echo.
echo Running full deployment preparation...
python scripts\deploy_manager.py --test --platform all --checklist
goto end

:end
echo.
echo ========================================
echo.
set /p continue="Press Enter to return to menu or type 'exit' to quit: "
if /i "%continue%"=="exit" goto exit
echo.
goto menu

:exit
echo.
echo Goodbye!
pause
