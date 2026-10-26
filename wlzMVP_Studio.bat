@echo off
title WLZ CS2 Workshop MVP Studio
cd /d "%~dp0"

python wlz_mvp_studio.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] An issue occurred during processing.
    pause
) else (
    echo.
    echo [DONE] Finished!
    pause
)
