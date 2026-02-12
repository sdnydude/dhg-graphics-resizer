@echo off
REM ============================================================
REM DHG Graphics Resizer — Windows
REM Double-click in File Explorer to launch.
REM
REM First run: creates .venv and installs all dependencies.
REM Subsequent runs: launches instantly.
REM ============================================================

cd /d "%~dp0"
set VENV_DIR=.venv
set DEPS_FLAG=.venv\.deps_installed

REM --- Find Python 3 ---
set PYTHON=
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "delims=" %%i in ('python -c "import sys; print(sys.version_info.major)"') do set PY_MAJ=%%i
    if "%PY_MAJ%"=="3" (set PYTHON=python& goto :found)
)
where python3 >nul 2>&1
if %ERRORLEVEL%==0 (set PYTHON=python3& goto :found)
where py >nul 2>&1
if %ERRORLEVEL%==0 (set PYTHON=py -3& goto :found)

echo.
echo  ============================================================
echo   Python 3 is not installed.
echo.
echo   Download from: https://www.python.org/downloads/
echo.
echo   IMPORTANT: Check "Add Python to PATH" during installation.
echo  ============================================================
echo.
pause
exit /b 1

:found
echo Python: %PYTHON%

REM --- Create venv on first run ---
if exist "%VENV_DIR%\Scripts\python.exe" goto :check_deps

echo.
echo  ============================================================
echo   First run - setting up environment (~60 seconds)
echo  ============================================================
echo.

echo Creating virtual environment...
%PYTHON% -m venv "%VENV_DIR%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo  Failed to create virtual environment.
    pause
    exit /b 1
)

:check_deps
if exist "%DEPS_FLAG%" goto :run

echo Installing dependencies (one-time)...
"%VENV_DIR%\Scripts\pip" install --quiet --upgrade pip

echo   - Pillow (image processing)...
"%VENV_DIR%\Scripts\pip" install --quiet Pillow
if %ERRORLEVEL% neq 0 (
    echo  Failed to install Pillow.
    pause
    exit /b 1
)

echo   - rembg (AI background removal)...
"%VENV_DIR%\Scripts\pip" install --quiet rembg onnxruntime
if %ERRORLEVEL% neq 0 (
    echo  Failed to install rembg.
    pause
    exit /b 1
)

REM Mark deps as installed
echo %DATE% %TIME% > "%DEPS_FLAG%"
echo.
echo  Setup complete!
echo.

:run
"%VENV_DIR%\Scripts\python" batch_resize_headshots.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred. Press any key to close...
    pause >nul
)
