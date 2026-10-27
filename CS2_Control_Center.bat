@echo off
title CS2 Server Control Center
cd /d "%~dp0"

echo ========================================================
echo           CS2 Server Control Center (Active)
echo ========================================================
echo.
echo [*] Launching application and opening interface...
echo.

python cs2_control_center.py %*

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Control Center exited with code %errorlevel%.
    pause
)
