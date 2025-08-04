@echo off
echo ========================================
echo Traqify Personal Finance Dashboard Builder
echo Using py-auto-to-exe with Enhanced Features
echo ========================================
echo.

:: Change to the project root directory
cd /d "%~dp0\.."

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found:
python --version

:: Check Python version (require 3.8+)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Checking Python version compatibility...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.8 or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)
echo SUCCESS: Python version is compatible

:: Install/update required build dependencies
echo.
echo Checking and installing build dependencies...
python -m pip install --upgrade pip
python -m pip install auto-py-to-exe>=2.46.0

:: Validate build configuration before starting
echo.
echo Validating build configuration...
python build_scripts\validate_build_config.py
if errorlevel 1 (
    echo ERROR: Build configuration validation failed
    echo Please fix the configuration issues and try again
    pause
    exit /b 1
)
echo SUCCESS: Build configuration validated successfully

:: Create necessary directories
if not exist "logs" mkdir logs
if not exist "dist" mkdir dist

:: Run the build script
echo.
echo Starting enhanced build process...
echo This may take several minutes depending on your system...
python build_scripts\py_auto_to_exe_build.py

if errorlevel 1 (
    echo.
    echo ERROR: BUILD FAILED!
    echo Check the log files in the logs directory for details
    echo Common issues:
    echo   - Missing dependencies in requirements.txt
    echo   - Module import errors
    echo   - Insufficient disk space
    echo   - Antivirus interference
) else (
    echo.
    echo SUCCESS: BUILD COMPLETED SUCCESSFULLY!
    echo.
    echo Build output location: dist\Traqify\
    echo Main executable: dist\Traqify\Traqify.exe
    echo Quick launcher: dist\Traqify\run.bat
    echo.
    echo Next steps:
    echo   1. Test the application: dist\Traqify\Traqify.exe
    echo   2. Create installer: Run Inno Setup with build_scripts\traqify_installer.iss
    echo   3. Distribute: Share the dist\Traqify folder or installer
    echo.
    echo New features included in this build:
    echo   - Advanced analytics and portfolio analysis
    echo   - Smart dashboard with AI insights
    echo   - Enhanced investment tracking with mutual funds
    echo   - Loan management with amortization tables
    echo   - Improved theme system and UI components
)

echo.
echo Press any key to exit...
pause >nul
