@echo off
title AI Reader - Building EXE
echo.
echo ========================================================
echo   AI Reader v3 - Building AIMP-Style Native App
echo ========================================================
echo.

cd /d "%~dp0"

:: Activate venv
call venv\Scripts\activate.bat

:: Build with PyInstaller
echo [1/2] Building AI Reader.exe ...
echo       This may take a few minutes...
echo.
pyinstaller AIReader.spec --noconfirm

echo.
if exist "dist\AI Reader\AI Reader.exe" (
    echo ========================================================
    echo   BUILD SUCCESSFUL!
    echo ========================================================
    echo.
    echo   Your app is ready at:
    echo   dist\AI Reader\AI Reader.exe
    echo.
    echo   You can copy the entire "dist\AI Reader" folder
    echo   anywhere and double-click "AI Reader.exe" to run.
    echo ========================================================
) else (
    echo ========================================================
    echo   BUILD FAILED - Check the output above for errors.
    echo ========================================================
)

echo.
pause
