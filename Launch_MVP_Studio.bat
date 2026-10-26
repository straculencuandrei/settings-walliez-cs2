@echo off
title CS2 MVP Anthem Studio
cd /d "%~dp0"
echo ========================================================
echo         CS2 MVP Anthem Visual Web Studio
echo ========================================================
echo.
echo [*] Launching studio and opening your web browser...
echo [*] Press Ctrl+C in this terminal window when done.
echo.
python add_mvp_ui.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Studio exited with code %errorlevel%.
    pause
)
