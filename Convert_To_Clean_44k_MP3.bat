@echo off
setlocal
cd /d "%~dp0"
title Clean 44.1kHz MP3 Converter (onlineaudioconverter.com algorithm)

if "%~1"=="" (
    echo =========================================================================
    echo   Clean 44.1kHz MP3 Audio Converter (onlineaudioconverter.com algorithm)
    echo =========================================================================
    echo.
    echo Drag and drop any audio files or folders directly onto this .bat file!
    echo Or enter file path below:
    echo.
    set /p "TARGET_PATH=Enter audio file path: "
    if "%TARGET_PATH%"=="" goto :eof
    python export_clean_mp3.py "%TARGET_PATH%"
    goto :end
)

python export_clean_mp3.py %*

:end
echo.
echo =========================================================================
echo Conversion Complete!
echo =========================================================================
pause
