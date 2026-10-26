@echo off
title CS2 MVP Anthem Sync
cd /d "%~dp0"
echo ========================================================
echo         CS2 MVP Anthem 1-Click Game Sync
echo ========================================================
echo.
python sync_client_anthems.py
if %errorlevel% neq 0 (
    echo [!] Python sync encountered an error.
)
echo.
pause
