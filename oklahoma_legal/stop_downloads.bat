@echo off
taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *monitor_and_download*" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo Download process stopped
) else (
    taskkill /F /IM python.exe
    echo All Python processes stopped
)
