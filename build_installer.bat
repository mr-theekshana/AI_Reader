@echo off
title AI Reader — Build Installer
echo.
echo ============================================================
echo   AI Reader v3 — Full Build + Installer Pipeline (Windows)
echo ============================================================
echo.

cd /d "%~dp0"

:: Check for PowerShell
where powershell >nul 2>nul
if errorlevel 1 (
    echo [ERROR] PowerShell not found! This build requires PowerShell.
    pause
    exit /b 1
)

:: Run the robust PowerShell build script
powershell -ExecutionPolicy Bypass -File "build.ps1"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the logs above.
    pause
    exit /b 1
)

echo.
pause
exit /b 0
